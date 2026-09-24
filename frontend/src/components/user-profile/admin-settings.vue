<template>
    <div class="row">
        <div style="width: 300px">
            <q-btn
                label="重置 S3 标签"
                class="button-border bg-button-primary full-width"
                icon="sym_o_sell"
                flat
                @click="resetS3Tagging"
            />
            <div class="help-text q-pt-sm">
                此操作将删除系统中所有文件的 S3 标签，并根据当前数据库状态重新生成。此操作不可撤销，且没有确认提示！
            </div>
        </div>
        <div style="width: 300px; margin-left: 20px">
            <q-btn
                label="重新计算文件大小"
                class="button-border bg-button-primary full-width"
                icon="sym_o_expand"
                flat
                @click="resetFileSizes"
            />
            <div class="help-text q-pt-sm">
                此操作将通过向 S3 查询每个文件的大小来重新计算数据库中的文件大小。此操作不可撤销，且没有确认提示！
            </div>
        </div>

        <div style="width: 300px; margin-left: 20px">
            <q-btn
                label="重新计算哈希"
                class="button-border bg-button-primary full-width"
                icon="sym_o_fingerprint"
                flat
                @click="recalculateHashes"
            />
            <div class="help-text q-pt-sm">
                此操作将从 S3 中提取文件的 MD5 哈希并存储到数据库。此操作不可撤销，且没有确认提示！
            </div>
        </div>

        <div style="width: 300px; margin-left: 20px">
            <q-btn
                label="修复缺失主题"
                class="button-border bg-button-primary full-width"
                icon="sym_o_topic"
                flat
                @click="reextractTopics"
            />
            <div class="help-text q-pt-sm">
                查找所有健康但主题数为 0 的 .bag 文件，并重新运行元数据提取（不进行转换）。
            </div>
        </div>
    </div>
</template>
<script setup lang="ts">
import type { RecalculateHashesResponseDto } from '@rslstudio/api-dto';
import { useQuasar } from 'quasar';
import axios from 'src/api/axios';

const $q = useQuasar();

async function resetS3Tagging(): Promise<void> {
    await axios.post('file/resetS3Tags');

    $q.notify({
        message: '已开始重置 S3 标签',
        color: 'positive',
        position: 'bottom',
        timeout: 2000,
    });
}

async function resetFileSizes(): Promise<void> {
    await axios.post('file/recomputeFileSizes');

    $q.notify({
        message: '已开始重新计算文件大小',
        color: 'positive',
        position: 'bottom',
        timeout: 2000,
    });
}

async function recalculateHashes(): Promise<void> {
    const { data } = await axios.post<RecalculateHashesResponseDto>(
        'files/maintenance/recalculate-hashes',
    );

    $q.notify({
        message: `已开始重新计算哈希，待处理 ${String(data.fileCount)} 个文件`,
        color: 'positive',
        position: 'bottom',
        timeout: 2000,
    });
}

async function reextractTopics(): Promise<void> {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const { data } = await axios.post('files/reextractTopics');

    $q.notify({
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/restrict-template-expressions
        message: `已开始主题提取，已加入队列 ${data.count} 个文件`,
        color: 'positive',
        position: 'bottom',
        timeout: 3000,
    });
}
</script>
