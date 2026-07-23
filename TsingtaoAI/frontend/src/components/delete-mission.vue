<template>
    <q-card-section class="q-pa-md">
        <p>
            请输入任务名称确认删除:
            <b>{{ mission.name }}</b>
        </p>
        <q-input
            v-model="missionNameCheck"
            outlined
            placeholder="输入任务名称确认"
            autofocus
        />
    </q-card-section>
</template>
<script setup lang="ts">
import type { MissionWithFilesDto } from '@kleinkram/api-dto/types/mission/mission-with-files.dto';
import { useQueryClient } from '@tanstack/vue-query';
import { AxiosError } from 'axios';
import { Notify } from 'quasar';
import ROUTES from 'src/router/routes';
import { deleteMission } from 'src/services/mutations/mission';
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const missionNameCheck = ref('');
const client = useQueryClient();
const properties = defineProps<{
    mission: MissionWithFilesDto;
}>();

const route = useRoute();
const router = useRouter();

const deleteMissionAction = async (): Promise<void> => {
    if (missionNameCheck.value === properties.mission.name) {
        await deleteMission(properties.mission)
            .then(async () => {
                await client.invalidateQueries({
                    predicate: (query) =>
                        query.queryKey[0] === 'missions' ||
                        (query.queryKey[0] === 'mission' &&
                            query.queryKey[1] === properties.mission.uuid),
                });

                await client.invalidateQueries({
                    predicate: (query) =>
                        query.queryKey[0] === 'projects' ||
                        (query.queryKey[0] === 'project' &&
                            query.queryKey[1] ===
                                properties.mission.project.uuid),
                });

                Notify.create({
                    message: '任务已删除',
                    color: 'positive',
                    timeout: 2000,
                    position: 'bottom',
                });

                if (route.name === ROUTES.FILES.routeName) {
                    await router.push({
                        name: ROUTES.MISSIONS.routeName,
                        params: {
                            projectUuid: route.params.projectUuid,
                        },
                    });
                }
            })
            .catch((error: unknown) => {
                let errorMessage = '';

                if (error instanceof AxiosError) {
                    if (error.response) {
                        const status = error.response.status;
                        if (status === 403) {
                            errorMessage = '无权限删除任务.';
                        } else if (status === 409) {
                            errorMessage = '任务内仍存在文件，无法删除.';
                        } else {
                            // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
                            errorMessage = `服务器返回错误码: ${status}`;
                        }
                    } else if (error.request) {
                        errorMessage = '服务器无响应';
                    } else {
                        errorMessage = error.message;
                    }
                } else if (error instanceof Error) {
                    errorMessage = error.message;
                } else {
                    errorMessage = '未知删除错误';
                }

                Notify.create({
                    message: `删除任务失败: ${errorMessage}`,
                    color: 'negative',
                    position: 'bottom',
                });
            });
    }
};

defineExpose({
    deleteMissionAction,

    // eslint-disable-next-line @typescript-eslint/naming-convention
    mission_name_check: missionNameCheck,
});
</script>
<style scoped></style>
