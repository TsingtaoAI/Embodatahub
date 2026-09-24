import {
    CleaningStatus,
    RdsCleaningResultEntity,
    RdsDatasetEntity,
    RdsEpisodeEntity,
    RdsFilterResultEntity,
    ProjectEntity,
} from '@rslstudio/backend-common';
// RDS service: handles dataset metadata, cleaning & filter result persistence
import {
    CreateRdsDatasetDto,
    CreateRdsFilterResultDto,
    RdsCleaningResultDto,
    RdsCleaningSummaryDto,
    RdsDatasetDto,
    RdsDatasetSummaryDto,
    RdsEpisodeDto,
    RdsFilterResultDto,
    SaveRdsResultsDto,
} from '@rslstudio/api-dto';
import {
    Injectable,
    NotFoundException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { DataSource, Repository } from 'typeorm';

function datasetEntityToDto(entity: RdsDatasetEntity): RdsDatasetDto {
    return {
        uuid: entity.uuid,
        createdAt: entity.createdAt,
        updatedAt: entity.updatedAt,
        name: entity.name,
        path: entity.path,
        format: entity.format,
        version: entity.version,
        totalEpisodes: entity.totalEpisodes,
        totalFrames: entity.totalFrames,
        fps: entity.fps,
        robotType: entity.robotType,
        videoKeys: entity.videoKeys,
        features: entity.features,
        episodes: entity.episodes?.map(episodeEntityToDto),
        cleaningResults: entity.cleaningResults?.map(cleaningResultEntityToDto),
        filterResults: entity.filterResults?.map(filterResultEntityToDto),
    };
}

function datasetEntityToSummary(entity: RdsDatasetEntity): RdsDatasetSummaryDto {
    const results = entity.cleaningResults ?? [];
    return {
        uuid: entity.uuid,
        name: entity.name,
        format: entity.format,
        totalEpisodes: entity.totalEpisodes,
        totalFrames: entity.totalFrames,
        fps: entity.fps,
        robotType: entity.robotType,
        passedCount: results.filter((r) => r.status === 'passed').length,
        reviewCount: results.filter((r) => r.status === 'review').length,
        excludedCount: results.filter((r) => r.status === 'excluded').length,
        unscoredCount: results.filter((r) => r.status === 'unscored').length,
        createdAt: entity.createdAt,
    };
}

function episodeEntityToDto(entity: RdsEpisodeEntity): RdsEpisodeDto {
    return {
        uuid: entity.uuid,
        episodeIndex: entity.episodeIndex,
        durationSeconds: entity.durationSeconds,
        length: entity.length,
        tasks: entity.tasks,
        subtasks: entity.subtasks,
        dataFile: entity.dataFile,
        videoFiles: entity.videoFiles,
    };
}

function cleaningResultEntityToDto(entity: RdsCleaningResultEntity): RdsCleaningResultDto {
    return {
        uuid: entity.uuid,
        episodeIndex: entity.episodeIndex,
        score: entity.score,
        status: entity.status,
        source: entity.source,
        perAttributeScores: entity.perAttributeScores,
        findings: entity.findings,
        reviewNote: entity.reviewNote,
        scorerVersion: entity.scorerVersion,
    };
}

function filterResultEntityToDto(entity: RdsFilterResultEntity): RdsFilterResultDto {
    return {
        uuid: entity.uuid,
        episodeIndex: entity.episodeIndex,
        stageId: entity.stageId,
        count: entity.count,
        skippedReason: entity.skippedReason,
        findings: entity.findings,
    };
}

@Injectable()
export class RdsService {
    constructor(
        @InjectRepository(RdsDatasetEntity)
        private datasetRepository: Repository<RdsDatasetEntity>,
        @InjectRepository(RdsFilterResultEntity)
        private filterResultRepository: Repository<RdsFilterResultEntity>,
        @InjectRepository(ProjectEntity)
        private projectRepository: Repository<ProjectEntity>,
        private readonly dataSource: DataSource,
    ) {}

    /** 创建数据集记录（RDS Python 导入后调用） */
    async createDataset(dto: CreateRdsDatasetDto): Promise<RdsDatasetDto> {
        const project = await this.projectRepository.findOneOrFail({
            where: { uuid: dto.projectUuid },
        });

        const dataset = this.datasetRepository.create({
            name: dto.name,
            path: dto.path,
            format: dto.format,
            version: dto.version,
            totalEpisodes: dto.totalEpisodes,
            totalFrames: dto.totalFrames,
            fps: dto.fps,
            robotType: dto.robotType,
            videoKeys: dto.videoKeys ?? null,
            features: dto.features ?? null,
            project,
        });

        const saved = await this.datasetRepository.save(dataset);
        return datasetEntityToDto(saved);
    }

    /** 保存完整的结构化处理结果（RDS Python 回写） */
    async saveResults(datasetUuid: string, dto: SaveRdsResultsDto): Promise<RdsDatasetDto> {
        return this.dataSource.transaction(async (manager) => {
            const dataset = await manager.findOneOrFail(RdsDatasetEntity, {
                where: { uuid: datasetUuid },
            });

            // 更新数据集元信息
            if (dto.dataset) {
                dataset.totalEpisodes = dto.dataset.totalEpisodes;
                dataset.totalFrames = dto.dataset.totalFrames;
                dataset.fps = dto.dataset.fps;
                await manager.save(RdsDatasetEntity, dataset);
            }

            // 保存 Episodes
            if (dto.episodes?.length) {
                await manager.delete(RdsEpisodeEntity, { dataset: { uuid: datasetUuid } });
                const episodes = dto.episodes.map((ep) => {
                    const entity = new RdsEpisodeEntity();
                    entity.dataset = dataset;
                    entity.episodeIndex = ep.episodeIndex;
                    entity.durationSeconds = ep.durationSeconds;
                    entity.length = ep.length;
                    entity.tasks = ep.tasks ?? null;
                    entity.subtasks = ep.subtasks ?? null;
                    entity.dataFile = ep.dataFile;
                    entity.videoFiles = ep.videoFiles ?? null;
                    return entity;
                });
                await manager.save(RdsEpisodeEntity, episodes);
            }

            // 保存清洗结果
            if (dto.cleaningResults?.length) {
                await manager.delete(RdsCleaningResultEntity, { dataset: { uuid: datasetUuid } });
                const results = dto.cleaningResults.map((r) => {
                    const entity = new RdsCleaningResultEntity();
                    entity.dataset = dataset;
                    entity.episodeIndex = r.episodeIndex;
                    entity.score = r.score ?? null;
                    entity.status = (r.status as CleaningStatus) ?? 'unscored';
                    entity.source = r.source;
                    entity.perAttributeScores = r.perAttributeScores ?? null;
                    entity.findings = r.findings ?? null;
                    entity.reviewNote = r.reviewNote ?? null;
                    entity.scorerVersion = r.scorerVersion;
                    return entity;
                });
                await manager.save(RdsCleaningResultEntity, results);
            }

            // 保存过滤结果
            if (dto.filterResults?.length) {
                await manager.delete(RdsFilterResultEntity, { dataset: { uuid: datasetUuid } });
                const filters = dto.filterResults.map((f) => {
                    const entity = new RdsFilterResultEntity();
                    entity.dataset = dataset;
                    entity.episodeIndex = f.episodeIndex;
                    entity.stageId = f.stageId;
                    entity.count = f.count;
                    entity.skippedReason = f.skippedReason ?? '';
                    entity.findings = f.findings ?? null;
                    return entity;
                });
                await manager.save(RdsFilterResultEntity, filters);
            }

            return manager.findOneOrFail(RdsDatasetEntity, {
                where: { uuid: datasetUuid },
                relations: ['episodes', 'cleaningResults', 'filterResults'],
            });
        }).then((entity) => datasetEntityToDto(entity));
    }

    /** 获取项目下的所有数据集摘要 */
    async getDatasetsByProject(projectUuid: string): Promise<RdsDatasetSummaryDto[]> {
        const project = await this.projectRepository.findOneOrFail({
            where: { uuid: projectUuid },
        });

        const datasets = await this.datasetRepository.find({
            where: { project: { uuid: project.uuid } },
            relations: ['cleaningResults'],
        });

        return datasets.map(datasetEntityToSummary);
    }

    /** 获取数据集详情（含 episodes 和结果） */
    async getDataset(uuid: string): Promise<RdsDatasetDto> {
        const dataset = await this.datasetRepository.findOneOrFail({
            where: { uuid },
            relations: ['episodes', 'cleaningResults', 'filterResults'],
        });

        return datasetEntityToDto(dataset);
    }

    /** 删除数据集 */
    async deleteDataset(uuid: string): Promise<void> {
        const result = await this.datasetRepository.softDelete(uuid);
        if (result.affected === 0) {
            throw new NotFoundException(`数据集 ${uuid} 未找到`);
        }
    }

    /** 获取清洗摘要 */
    async getCleaningSummary(datasetUuid: string): Promise<RdsCleaningSummaryDto> {
        const dataset = await this.datasetRepository.findOneOrFail({
            where: { uuid: datasetUuid },
            relations: ['cleaningResults'],
        });

        const results = (dataset.cleaningResults ?? []).map(cleaningResultEntityToDto);
        const scored = results.filter((r) => r.score !== null && r.score !== undefined);
        const averageScore = scored.length > 0
            ? scored.reduce((sum, r) => sum + (r.score ?? 0), 0) / scored.length
            : 0;

        return {
            total: results.length,
            passedCount: results.filter((r) => r.status === 'passed').length,
            reviewCount: results.filter((r) => r.status === 'review').length,
            excludedCount: results.filter((r) => r.status === 'excluded').length,
            unscoredCount: results.filter((r) => r.status === 'unscored').length,
            averageScore,
            scorerVersion: results[0]?.scorerVersion ?? '',
            results,
        };
    }

    /** 保存过滤结果 */
    async saveFilterResults(
        datasetUuid: string,
        results: CreateRdsFilterResultDto[],
    ): Promise<RdsFilterResultDto[]> {
        const dataset = await this.datasetRepository.findOneOrFail({
            where: { uuid: datasetUuid },
        });

        return this.dataSource.transaction(async (manager) => {
            await manager.delete(RdsFilterResultEntity, { dataset: { uuid: datasetUuid } });
            const entities = results.map((r) =>
                manager.create(RdsFilterResultEntity, {
                    ...r,
                    dataset,
                }),
            );
            const saved = await manager.save(RdsFilterResultEntity, entities);
            return saved.map(filterResultEntityToDto);
        });
    }

    /** 获取过滤结果 */
    async getFilterResults(datasetUuid: string): Promise<RdsFilterResultDto[]> {
        const results = await this.filterResultRepository.find({
            where: { dataset: { uuid: datasetUuid } },
        });

        return results.map(filterResultEntityToDto);
    }
}
