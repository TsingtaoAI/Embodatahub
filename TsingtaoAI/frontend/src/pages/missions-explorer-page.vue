<template>
    <div>
        <title-section :title="project?.name">
            <template #subtitle>
                <span>
                    {{ project?.description }}
                </span>
            </template>

            <template #buttons>
                <button-group>
                    <q-btn
                        class="button-border"
                        flat
                        style="height: 100%"
                        color="primary"
                        icon="sym_o_checklist"
                        :label="$t('project.datasets')"
                        @click="navigateToDatasets"
                    />

                    <ConfigureTagsDialogOpener
                        v-if="projectUuid"
                        :project-uuid="projectUuid"
                    >
                        <q-btn
                            class="button-border"
                            flat
                            style="height: 100%"
                            color="primary"
                            icon="sym_o_sell"
                            label="强制元数据"
                            :disable="!projectUuid"
                        />
                    </ConfigureTagsDialogOpener>

                    <q-btn
                        icon="sym_o_more_vert"
                        class="button-border"
                        flat
                        style="height: 100%"
                        color="primary"
                    >
                        <q-tooltip> 更多操作</q-tooltip>

                        <q-menu
                            v-if="projectUuid !== undefined"
                            auto-close
                            style="width: 280px"
                        >
                            <q-list>
                                <change-project-rights-dialog-opener
                                    :project-uuid="projectUuid"
                                    project-access-uuid=""
                                >
                                    <q-item v-close-popup clickable>
                                        <q-item-section avatar>
                                            <q-icon name="sym_o_lock" />
                                        </q-item-section>
                                        <q-item-section>
                                            <q-item-section>
                                                管理权限
                                            </q-item-section>
                                        </q-item-section>
                                    </q-item>
                                </change-project-rights-dialog-opener>

                                <edit-project-dialog-opener
                                    :project-uuid="projectUuid"
                                >
                                    <q-item v-close-popup clickable>
                                        <q-item-section avatar>
                                            <q-icon name="sym_o_edit" />
                                        </q-item-section>
                                        <q-item-section>
                                            <q-item-section>
                                                编辑项目
                                            </q-item-section>
                                        </q-item-section>
                                    </q-item>
                                </edit-project-dialog-opener>
                                <q-item
                                    v-ripple
                                    clickable
                                    @click="copyProjectUuidToClipboard"
                                >
                                    <q-item-section avatar>
                                        <q-icon name="sym_o_fingerprint" />
                                    </q-item-section>
                                    <q-item-section> 复制 UUID</q-item-section>
                                </q-item>
                                <DeleteProjectDialogOpener
                                    :project-uuid="projectUuid ?? ''"
                                    :has-missions="
                                        (project?.missionCount ?? 0) > 0
                                    "
                                >
                                    <q-item
                                        v-ripple
                                        v-close-popup
                                        clickable
                                        style="color: red"
                                    >
                                        <q-item-section avatar>
                                            <q-icon name="sym_o_delete" />
                                        </q-item-section>
                                        <q-item-section>
                                            <q-item-section>
                                                删除项目
                                            </q-item-section>
                                        </q-item-section>
                                    </q-item>
                                </DeleteProjectDialogOpener>
                            </q-list>
                        </q-menu>
                    </q-btn>
                </button-group>
            </template>
        </title-section>
        <ActionConfiguration
            :open="createAction"
            :mission-uuids="selectedMissionUuids"
            @close="onClose"
        />
        <div>
            <div
                v-if="selectedMissions.length === 0"
                class="q-my-lg flex justify-between items-center"
            >
                <h2 class="text-h4 q-mb-xs">
                    All Missions of {{ project?.name }}
                </h2>

                <button-group>
                    <app-search-bar
                        v-model="search"
                        placeholder="按任务名称搜索"
                    />

                    <app-refresh-button @click="refresh" />
                    <UploadMissionFolder :project-uuid="projectUuid">
                        <q-btn
                            flat
                            style="height: 100%"
                            color="icon-secondary"
                            class="button-border"
                            icon="sym_o_drive_folder_upload"
                        />
                    </UploadMissionFolder>
                    <create-mission-dialog-opener :project-uuid="projectUuid">
                        <app-create-button label="创建任务" />
                    </create-mission-dialog-opener>
                </button-group>
            </div>
            <div v-else class="q-py-lg" style="background: #0f62fe">
                <ButtonGroupOverlay>
                    <template #start>
                        <div style="margin: 0; font-size: 14pt; color: white">
                            {{ selectedMissions.length }}
                            个任务
                            已选中
                        </div>
                    </template>
                    <template #end>
                        <KleinDownloadMissions
                            :missions="selectedMissions"
                            style="max-width: 400px"
                        />
                        <q-btn
                            flat
                            dense
                            padding="6px"
                            icon="sym_o_analytics"
                            color="white"
                            @click="openMultiActions"
                        >
                            操作
                        </q-btn>

                        <q-btn
                            flat
                            dense
                            padding="6px"
                            icon="sym_o_delete"
                            color="white"
                            :disable="
                                selectedMissions.length !== 1 ||
                                (selectedMissions.length === 1 &&
                                    (selectedMissions[0]?.filesCount ?? 0) > 0)
                            "
                            @click="deleteMission"
                        >
                            删除
                            <q-tooltip v-if="selectedMissions.length !== 1">
                                一次只能删除一个任务
                            </q-tooltip>

                            <q-tooltip
                                v-if="
                                    selectedMissions.length === 1 &&
                                    (selectedMissions[0]?.filesCount ?? 0) > 0
                                "
                            >
                                不能删除包含文件的任务
                            </q-tooltip>
                        </q-btn>
                        <q-btn
                            flat
                            dense
                            padding="6px"
                            icon="sym_o_close"
                            color="white"
                            @click="deselect"
                        />
                    </template>
                </ButtonGroupOverlay>
            </div>

            <div>
                <Suspense>
                    <template #fallback>
                        <div style="width: 550px; height: 67px">
                            <q-skeleton
                                class="q-mr-md q-mb-sm q-mt-sm"
                                style="width: 300px; height: 20px"
                            />
                            <q-skeleton
                                class="q-mr-md"
                                style="width: 200px; height: 18px"
                            />
                        </div>
                    </template>
                </Suspense>
            </div>
            <div>
                <Suspense>
                    <explorer-page-mission-table
                        v-model:selected="selectedMissions"
                    />
                </Suspense>
            </div>
        </div>
    </div>
</template>
<script setup lang="ts">
import type { FlatMissionDto } from '@rslstudio/api-dto/types/mission/mission.dto';
import { useQueryClient } from '@tanstack/vue-query';
import ActionConfiguration from 'components/actions/action-configuration.vue';
import DeleteProjectDialogOpener from 'components/button-wrapper/delete-project-dialog-opener.vue';
import ChangeProjectRightsDialogOpener from 'components/button-wrapper/dialog-opener-change-project-rights.vue';
import ConfigureTagsDialogOpener from 'components/button-wrapper/dialog-opener-configure-tags.vue';
import CreateMissionDialogOpener from 'components/button-wrapper/dialog-opener-create-mission.vue';
import EditProjectDialogOpener from 'components/button-wrapper/edit-project-dialog-opener.vue';
import ButtonGroupOverlay from 'components/buttons/button-group-overlay.vue';
import ButtonGroup from 'components/buttons/button-group.vue';
import KleinDownloadMissions from 'components/cli-links/klein-download-missions.vue';
import AppCreateButton from 'components/common/app-create-button.vue';
import AppRefreshButton from 'components/common/app-refresh-button.vue';
import AppSearchBar from 'components/common/app-search-bar.vue';
import ExplorerPageMissionTable from 'components/explorer-page/explorer-page-mission-table.vue';
import TitleSection from 'components/title-section.vue';
import UploadMissionFolder from 'components/upload-mission-folder.vue';
import { copyToClipboard, useQuasar } from 'quasar';
import DeleteMissionDialog from 'src/dialogs/delete-mission-dialog.vue';
import {
    registerNoPermissionErrorHandler,
    useHandler,
    useProjectQuery,
} from 'src/hooks/query-hooks';
import { useProjectUUID } from 'src/hooks/router-hooks';
import { useRouter } from 'vue-router';
import ROUTES from 'src/router/routes';
import { computed, ref, Ref } from 'vue';

const queryClient = useQueryClient();
const handler = useHandler();
const $q = useQuasar();
const $router = useRouter();
const projectUuid = useProjectUUID();
const { data: project, isLoadingError, error } = useProjectQuery(projectUuid);
const createAction = ref(false);

registerNoPermissionErrorHandler(isLoadingError, projectUuid, 'project', error);

const navigateToDatasets = (): void => {
    void $router.push({
        name: ROUTES.PROJECT_DATASETS.routeName,
        params: { projectUuid: projectUuid.value },
    });
};

const onClose = (): void => {
    createAction.value = false;
};

const deleteMission = (): void => {
    const mission = selectedMissions.value[0];

    if (mission === undefined) {
        $q.notify({
            type: 'negative',
            message: '请选择要删除的任务',
        });
        return;
    }

    $q.dialog({
        title: '删除任务',
        component: DeleteMissionDialog,
        componentProps: {
            missionUuid: mission.uuid,
        },
    });

    deselect();
};

const selectedMissions: Ref<FlatMissionDto[]> = ref([]);

const search = computed({
    get: () => handler.value.searchParams.name,
    set: (value: string) => {
        handler.value.setSearch({ name: value });
    },
});

const selectedMissionUuids = computed(() => {
    return selectedMissions.value.map((mission) => mission.uuid);
});

async function refresh(): Promise<void> {
    await queryClient.invalidateQueries({
        queryKey: ['missions'],
    });
}

function deselect(): void {
    selectedMissions.value = [];
}

function openMultiActions(): void {
    createAction.value = true;
}

const copyProjectUuidToClipboard = async (): Promise<void> => {
    await copyToClipboard(projectUuid.value ?? '');
};
</script>
