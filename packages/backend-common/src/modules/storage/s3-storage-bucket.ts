import {
    DeleteObjectCommand,
    DeleteObjectTaggingCommand,
    GetObjectCommand,
    GetObjectTaggingCommand,
    HeadObjectCommand,
    ListObjectsV2Command,
    PutObjectCommand,
    PutObjectTaggingCommand,
    _Object,
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { Logger } from '@nestjs/common';
import axios from 'axios';
import { createReadStream, createWriteStream } from 'node:fs';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { StorageAuthService } from './storage-auth.service';
import { S3ClientContainer } from './storage-config.factory';
import { MetricPoint, StorageMetricsService } from './storage-metrics.service';
import {
    IStorageBucket,
    StorageCredentials,
    StorageItem,
    StorageItemStat,
    StorageSystemMetrics,
} from './types';

export class S3StorageBucket implements IStorageBucket {
    constructor(
        private readonly bucketName: string,
        private readonly clients: S3ClientContainer,
        private readonly authService: StorageAuthService,
        private readonly metricsService?: StorageMetricsService,
    ) {}

    async getPresignedDownloadUrl(
        objectName: string,
        expirySeconds: number,
        responseDisposition?: Record<string, string>,
    ): Promise<string> {
        const command = new GetObjectCommand({
            Bucket: this.bucketName,
            Key: objectName,
            ResponseContentDisposition:
                responseDisposition?.['response-content-disposition'],
        });
        return getSignedUrl(this.clients.external, command, {
            expiresIn: expirySeconds,
        });
    }

    async getInternalPresignedDownloadUrl(
        objectName: string,
        expirySeconds: number,
        responseDisposition?: Record<string, string>,
    ): Promise<string> {
        const command = new GetObjectCommand({
            Bucket: this.bucketName,
            Key: objectName,
            ResponseContentDisposition:
                responseDisposition?.['response-content-disposition'],
        });
        return getSignedUrl(this.clients.internal, command, {
            expiresIn: expirySeconds,
        });
    }

    async downloadFile(
        objectName: string,
        destinationPath: string,
    ): Promise<void> {
        const command = new GetObjectCommand({
            Bucket: this.bucketName,
            Key: objectName,
        });
        const response = await this.clients.internal.send(command);
        if (response.Body instanceof Readable) {
            await pipeline(response.Body, createWriteStream(destinationPath));
        } else {
            throw new TypeError('S3 body is not a readable stream');
        }
    }

    async getFileStream(objectName: string): Promise<Readable> {
        const command = new GetObjectCommand({
            Bucket: this.bucketName,
            Key: objectName,
        });
        const response = await this.clients.internal.send(command);
        if (response.Body instanceof Readable) {
            return response.Body;
        }
        throw new TypeError('S3 body is not a readable stream');
    }

    async listFiles(): Promise<StorageItem[]> {
        const command = new ListObjectsV2Command({
            Bucket: this.bucketName,
        });
        const response = await this.clients.internal.send(command);
        return (
            response.Contents?.map((item: _Object) => ({
                name: item.Key ?? '',
                lastModified: item.LastModified ?? new Date(),
                etag: item.ETag ?? '',
                size: item.Size ?? 0,
            })) ?? []
        );
    }

    async getFileInfo(
        objectName: string,
    ): Promise<StorageItemStat | undefined> {
        const command = new HeadObjectCommand({
            Bucket: this.bucketName,
            Key: objectName,
        });
        try {
            const response = await this.clients.internal.send(command);
            return {
                size: response.ContentLength ?? 0,
                etag: response.ETag ?? '',
                lastModified: response.LastModified ?? new Date(),
                metaData: response.Metadata ?? {},
            };
        } catch (error: unknown) {
            if (
                error instanceof Error &&
                (error.name === 'NotFound' ||
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access
                    (error as any).$metadata?.httpStatusCode === 404)
            ) {
                return undefined;
            }
            throw error;
        }
    }

    async uploadFile(
        objectName: string,
        filePath: string,
        metaData?: Record<string, string>,
    ): Promise<void> {
        const command = new PutObjectCommand({
            Bucket: this.bucketName,
            Key: objectName,
            Body: createReadStream(filePath),
            Metadata: metaData,
        });
        await this.clients.internal.send(command);
    }

    async deleteFile(objectName: string): Promise<void> {
        const command = new DeleteObjectCommand({
            Bucket: this.bucketName,
            Key: objectName,
        });
        await this.clients.internal.send(command);
    }

    async getSystemMetrics(): Promise<StorageSystemMetrics> {
        // ── 尝试 Prometheus 指标 ──
        const raw = this.metricsService
            ? await this.metricsService.getSystemMetrics()
            : {};

        // ── MinIO 指标（优先）──
        const minioTotal = (raw.minio_cluster_capacity_usable_total_bytes as MetricPoint[] | undefined)?.[0]?.value;
        const minioFree = (raw.minio_cluster_capacity_usable_free_bytes as MetricPoint[] | undefined)?.[0]?.value;
        if (minioTotal !== undefined && minioTotal > 0) {
            return {
                usedBytes: minioFree !== undefined ? minioTotal - minioFree : 0,
                totalBytes: minioTotal,
                usedInodes: 0,
                totalInodes: 0,
            };
        }

        // Try standard SeaweedFS disk byte metrics (v3.x naming)
        const totalRaw = raw.seaweedfs_master_disk_total_bytes as
            | MetricPoint[]
            | undefined;
        const volRecord = raw.SeaweedFS_volumeServer_resource as
            | MetricPoint[]
            | undefined;

        const totalValue =
            totalRaw?.[0]?.value ??
            volRecord?.find((m) => m.labels.type === 'all')?.value;

        const freeRaw = raw.seaweedfs_master_disk_free_bytes as
            | MetricPoint[]
            | undefined;
        const freeValue =
            freeRaw?.[0]?.value ??
            volRecord?.find((m) => m.labels.type === 'free')?.value;

        // If standard metrics are available, use them directly
        if (totalValue !== undefined && freeValue !== undefined) {
            return {
                usedBytes: totalValue - freeValue,
                totalBytes: totalValue,
                usedInodes: 0,
                totalInodes: 0,
            };
        }

        // Fallback: parse sizelimit from SeaweedFS_build_info (e.g. "30GB")
        // and compute usage via volume ratio from metrics
        const buildInfo = raw.SeaweedFS_build_info as MetricPoint[] | undefined;
        const sizeLimit = buildInfo?.[0]?.labels?.sizelimit;
        const parsedTotal = sizeLimit ? parseSizeLimit(sizeLimit) : 0;

        // Try getting volume-level usage from volume server resource metrics
        const volumeUsed = volRecord?.find((m) => m.labels.type === 'used')?.value;
        const volumeMax = volRecord?.find((m) => m.labels.type === 'max')?.value;

        if (parsedTotal > 0 && volumeUsed !== undefined && volumeMax !== undefined && volumeMax > 0) {
            const usedBytes = Math.round((volumeUsed / volumeMax) * parsedTotal);
            return {
                usedBytes,
                totalBytes: parsedTotal,
                usedInodes: 0,
                totalInodes: 0,
            };
        }

        // ── 直接查询 SeaweedFS Master API ──
        // 当 Prometheus 指标不可用时（如系统刚启动），直接调用 /dir/status
        // 获取磁盘状态。此路径不依赖 Prometheus 数据。
        try {
            const diskStatus = await this.fetchDiskStatusFromMaster();
            if (diskStatus && diskStatus.totalBytes > 0) {
                return diskStatus;
            }
        } catch {
            Logger.warn(
                'Failed to fetch disk status from SeaweedFS master API.',
                'S3StorageBucket:getSystemMetrics',
            );
        }

        // ── 最终后备：通过 S3 ListObjects 计算实际存储用量 ──
        // 不依赖 Prometheus 或任何外部 API，仅需 S3 连接即可工作。
        // 适用于 MinIO、SeaweedFS 等所有 S3 兼容存储。
        try {
            const s3Metrics = await this.calculateUsageFromS3(parsedTotal);
            if (s3Metrics) return s3Metrics;
        } catch {
            Logger.warn(
                'Failed to calculate storage usage from S3 bucket listing.',
                'S3StorageBucket:getSystemMetrics',
            );
        }

        Logger.warn(
            'All storage metric sources failed. Storage capacity views may read zero.',
            'S3StorageBucket:getSystemMetrics',
        );

        return {
            usedBytes: 0,
            totalBytes: parsedTotal, // at least show the size limit if available
            usedInodes: 0,
            totalInodes: 0,
        };
    }

    /**
     * Fetch disk usage from SeaweedFS master /dir/status API
     */
    private async fetchDiskStatusFromMaster(): Promise<StorageSystemMetrics | null> {
        // SeaweedFS master API runs on port 9333, but S3_ENDPOINT_INTERNAL
        // typically points to the S3 gateway (port 9000).  Extract the hostname
        // and always use the master port.
        const internalHost = process.env.S3_ENDPOINT_INTERNAL ?? 'seaweedfs';
        const hostname = internalHost.split(':')[0];
        const masterUrl = `${hostname}:9333`;
        try {
            const response = await axios.get(`http://${masterUrl}/dir/status`, { timeout: 3000 });
            const data = response.data as {
                Topology?: {
                    Max?: number;
                    Free?: number;
                    DataCenters?: Array<{
                        Racks?: Array<{
                            DataNodes?: Array<{
                                Volumes?: number;
                                Max?: number;
                            }>;
                        }>;
                    }>;
                };
                Version?: string;
            };

            const topo = data.Topology;
            if (!topo) return null;

            // Parse total capacity from version string, e.g. "30GB 4.19 ..."
            const version = data.Version ?? '';
            const sizeMatch = version.match(/^(\d+)\s*(GB|TB)/i);
            let totalBytes = 0;
            if (sizeMatch) {
                const num = Number(sizeMatch[1]);
                const unit = sizeMatch[2].toUpperCase();
                totalBytes = unit === 'TB' ? num * 1024 * 1024 * 1024 * 1024 : num * 1024 * 1024 * 1024;
            }

            if (totalBytes === 0) return null;

            // Compute usage ratio from volumes
            const dataNode = topo.DataCenters?.[0]?.Racks?.[0]?.DataNodes?.[0];
            const nodeMax = dataNode?.Max ?? 0;
            if (dataNode && nodeMax > 0) {
                const usedVolumes = dataNode.Volumes ?? 0;
                const ratio = usedVolumes / nodeMax;
                return {
                    usedBytes: Math.round(ratio * totalBytes),
                    totalBytes,
                    usedInodes: 0,
                    totalInodes: 0,
                };
            }

            // Fallback: use topology Free/Max counts
            if (topo.Max && topo.Max > 0 && topo.Free !== undefined) {
                const usedRatio = (topo.Max - topo.Free) / topo.Max;
                return {
                    usedBytes: Math.round(usedRatio * totalBytes),
                    totalBytes,
                    usedInodes: 0,
                    totalInodes: 0,
                };
            }

            return null;
        } catch {
            return null;
        }
    }

    /**
     * Calculate storage usage by listing S3 bucket objects.
     * This is the most reliable fallback — it works with any S3-compatible
     * storage (MinIO, SeaweedFS, AWS S3, etc.) as long as the S3 connection
     * is healthy.
     *
     * @param knownTotal  total capacity from Prometheus (0 if unavailable)
     */
    private async calculateUsageFromS3(
        knownTotal: number,
    ): Promise<StorageSystemMetrics | null> {
        let totalSize = 0;
        let continuationToken: string | undefined;

        // Paginate through up to ~50,000 objects (5 pages of 1,000)
        for (let page = 0; page < 5; page++) {
            const command = new ListObjectsV2Command({
                Bucket: this.bucketName,
                MaxKeys: 1000,
                ...(continuationToken
                    ? { ContinuationToken: continuationToken }
                    : {}),
            });
            const response = await this.clients.internal.send(command);
            const contents = response.Contents ?? [];
            for (const obj of contents) {
                totalSize += obj.Size ?? 0;
            }
            if (!response.IsTruncated || !response.NextContinuationToken) {
                break;
            }
            continuationToken = response.NextContinuationToken;
        }

        // Try to get total capacity from env var if Prometheus didn't provide it
        const configuredTotal =
            knownTotal > 0
                ? knownTotal
                : parseInt(
                      process.env.S3_TOTAL_CAPACITY_BYTES ?? '0',
                      10,
                  );

        if (configuredTotal > 0 && totalSize > 0) {
            return {
                usedBytes: totalSize,
                totalBytes: configuredTotal,
                usedInodes: 0,
                totalInodes: 0,
            };
        }

        // If no total capacity is known but we have usage data,
        // report what we can (used bytes only matters visually)
        if (totalSize > 0) {
            Logger.log(
                `Bucket "${this.bucketName}" has ${totalSize} bytes used (no total capacity available).`,
                'S3StorageBucket',
            );
        }

        return null;
    }

    async getTags(objectName: string): Promise<Record<string, string>> {
        const command = new GetObjectTaggingCommand({
            Bucket: this.bucketName,
            Key: objectName,
        });
        const response = await this.clients.internal.send(command);
        const tags: Record<string, string> = {};
        if (response.TagSet) {
            for (const tag of response.TagSet) {
                if (tag.Key && tag.Value) {
                    tags[tag.Key] = tag.Value;
                }
            }
        }
        return tags;
    }

    async addTags(
        objectName: string,
        tags: Record<string, string>,
    ): Promise<void> {
        const command = new PutObjectTaggingCommand({
            Bucket: this.bucketName,
            Key: objectName,
            Tagging: {
                TagSet: Object.entries(tags).map(([key, value]) => ({
                    Key: key,
                    Value: value,
                })),
            },
        });
        await this.clients.internal.send(command);
    }

    async removeTags(objectName: string): Promise<void> {
        const command = new DeleteObjectTaggingCommand({
            Bucket: this.bucketName,
            Key: objectName,
        });
        await this.clients.internal.send(command);
    }

    async generateTemporaryCredential(
        filename: string, // This is usually the UUID/object name used for the ARN
    ): Promise<StorageCredentials> {
        return this.authService.generateTemporaryCredential(
            filename,
            this.bucketName,
        );
    }
}

/** Parse a SeaweedFS size-limit string like "30GB" or "1TB" into bytes */
function parseSizeLimit(value: string): number {
    const match = value.trim().match(/^(\d+(?:\.\d+)?)\s*(GB|TB|MB|PB)$/i);
    if (!match) return 0;
    const num = Number.parseFloat(match[1]);
    const unit = match[2].toUpperCase();
    switch (unit) {
        case 'PB': return num * 1024 * 1024 * 1024 * 1024 * 1024;
        case 'TB': return num * 1024 * 1024 * 1024 * 1024;
        case 'GB': return num * 1024 * 1024 * 1024;
        case 'MB': return num * 1024 * 1024;
        default: return 0;
    }
}
