<template>
    <div v-if="project">
        <label for="projectName">项目名称 *</label>
        <q-input
            ref="projectNameInput"
            v-model="projectName"
            name="projectName"
            outlined
            autofocus
            style="padding-bottom: 30px"
            placeholder="填写名称......"
            :rules="[
                (val) => !!val || '项目名称不能为空!',
                (val) => val.length <= 20 || '项目名称不能超过20个字符!',
                (val) => val.length >= 3 || '项目名称至少3个字符!',
                (val) => /^[a-zA-Z0-9-_]*$/.test(val) || `仅允许字母、数字、横杠、下划线，非法字符：${val.match(/[^a-zA-Z0-9-_]/g)?.map(c => `'${c}'`).join(', ') || ''}`,
                (val) => !invalidProjectNames.includes(val) || '该项目名称已存在!',
            ]"
            @update:model-value="onProjectNameUpdate"
        />

        <label for="projectDescription">项目描述 *</label>
        <q-input
            v-model="projectDescription"
            autofocus
            name="projectDescription"
            type="textarea"
            outlined
            placeholder="填写描述..."
            :rules="[(val) => !!val || '项目描述不能为空']"
            @update:model-value="onProjectNameUpdate"
        />

        <div class="flex column">
            <label for="autoConvert"
                >自动转换为 mcap 文件 *</label
            >
            <q-toggle
                v-model="autoConvert"
                name="autoConvert"
                label="开启自动转mcap格式"
                color="primary"
                dense
                style="margin: 10px 0"
            />
            <span class="text-grey-8">
                自动转换功能存在已知限制，详情查看：
                https://github.com/leggedrobotics/kleinkram/issues/1250.
            </span>
        </div>
    </div>
    <div v-else>
        <q-spinner />
    </div>
</template>
<script setup lang="ts">
import type { ProjectWithRequiredTagsDto } from '@kleinkram/api-dto/types/project/project-with-required-tags.dto';
import { useQueryClient } from '@tanstack/vue-query';
import { Notify, QInput } from 'quasar';
import { useProjectQuery } from 'src/hooks/query-hooks';
import { updateProject } from 'src/services/mutations/project';
import { computed, Ref, ref, watch } from 'vue';

const { projectUuid } = defineProps<{
    projectUuid: string;
}>();
const queryClient = useQueryClient();

const projectName = ref('');
const autoConvert = ref(true);
const projectDescription = ref('');
const hasValidInput = ref(false);

const invalidProjectNames: Ref<string[]> = ref([]);

const { data: project } = useProjectQuery(computed(() => projectUuid));

watch(
    () => project.value,
    (newVale: ProjectWithRequiredTagsDto | undefined) => {
        if (newVale) {
            projectName.value = newVale.name;
            projectDescription.value = newVale.description;
            autoConvert.value = newVale.autoConvert;
        }
    },
    { immediate: true },
);

// eslint-disable-next-line @typescript-eslint/naming-convention
async function save_changes(): Promise<void> {
    // resolve immediately if no changes
    if (
        projectName.value === project.value?.name &&
        projectDescription.value === project.value.description &&
        autoConvert.value === project.value.autoConvert
    )
        return;

    // validate input
    if (!project.value?.uuid) {
        throw new Error('项目UUID无效');
    }
    if (!project.value.name) {
        throw new Error('项目名称不能为空');
    }
    if (!project.value.description) {
        throw new Error('项目描述不能为空');
    }

    await updateProject(
        project.value.uuid,
        projectName.value.trim(),
        projectDescription.value,
        autoConvert.value,
    ).catch((error: unknown) => {
        let errorMessage = '';
        errorMessage =
            error instanceof Error
                ? error.message
                : ((error as { response?: { data?: { message?: string } } })
                      .response?.data?.message ?? '未知错误');

        if (errorMessage.includes('Project')) {
            Notify.create({
                message: `项目更新失败: ${errorMessage}`,
                color: 'negative',
                position: 'bottom',
                timeout: 5000,
            });
        } else {
            Notify.create({
                message: `项目更新失败: ${errorMessage}`,
                color: 'negative',
                position: 'bottom',
                timeout: 5000,
            });
        }

        throw error as Error;
    });

    const cache = queryClient.getQueryCache();
    const filtered = cache
        .getAll()
        .filter(
            (query) =>
                query.queryKey[0] === 'projects' ||
                query.queryKey[0] === 'project',
        );
    await Promise.all(
        filtered.map((query) =>
            queryClient.invalidateQueries({ queryKey: query.queryKey }),
        ),
    );

    Notify.create({
        message: '项目更新成功',
        color: 'positive',
        position: 'bottom',
        timeout: 2000,
    });
}

defineExpose({
    // eslint-disable-next-line @typescript-eslint/naming-convention
    save_changes,
});

const onProjectNameUpdate = () => {
    hasValidInput.value = !!projectName.value && !!projectDescription.value;
};
</script>
<style scoped></style>
