<template>
    <q-card-section class="q-pa-md">
        <p>
            请输入项目名称确认删除：:
            <b>{{ project.name }}</b>
        </p>
        <q-input
            v-model="projectNameCheck"
            outlined
            placeholder="输入项目名称确认"
            autofocus
        />
    </q-card-section>
</template>
<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query';
import { Notify, QInput } from 'quasar';
import { useHandler } from 'src/hooks/query-hooks';
import { deleteProject } from 'src/services/mutations/project';
import { ref } from 'vue';

import type { ProjectWithCreator } from '@kleinkram/api-dto/types/project/project-with-creator.dto';

const projectNameCheck = ref('');
const client = useQueryClient();
const { project } = defineProps<{
    project: ProjectWithCreator;
}>();

const handler = useHandler();

async function deleteProjectAction(): Promise<void> {
    if (projectNameCheck.value === project.name) {
        await deleteProject(project.uuid)
            .then(async () => {
                await client.invalidateQueries({
                    predicate: (query) =>
                        query.queryKey[0] === 'projects' ||
                        (query.queryKey[0] === 'project' &&
                            query.queryKey[1] === project.uuid),
                });
                Notify.create({
                    message: '项目已删除',
                    color: 'positive',
                    timeout: 2000,
                    position: 'bottom',
                });

                handler.value.setProjectUUID('');
            })
            .catch((error: unknown) => {
                let errorMessage = '';
                errorMessage =
                    error instanceof Error
                        ? error.message
                        : ((
                              error as {
                                  response?: { data?: { message?: string } };
                              }
                          ).response?.data?.message ?? '未知错误');

                Notify.create({
                    message: `删除项目失败: ${errorMessage}`,
                    color: 'negative',
                    position: 'bottom',
                });
            });
    }
}

defineExpose({
    deleteProjectAction,

    // eslint-disable-next-line @typescript-eslint/naming-convention
    project_name_check: projectNameCheck,
});
</script>
