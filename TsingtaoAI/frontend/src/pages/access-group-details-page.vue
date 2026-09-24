<template>
    <title-section :title="accessGroup?.name">
        <template #title>
            <div class="row items-center q-gutter-x-sm">
                <q-avatar
                    v-if="personal"
                    size="48px"
                    color="blue-1"
                    text-color="primary"
                >
                    <q-icon name="sym_o_person" />
                </q-avatar>
                <q-avatar v-else size="48px" color="grey-2" text-color="grey-8">
                    <q-icon name="sym_o_group" />
                </q-avatar>
                <div class="column q-ml-sm">
                    <h1 class="text-h5 text-md-h3 q-ma-none ellipsis">
                        {{ accessGroup?.name ?? '加载中...' }}
                    </h1>
                    <q-chip
                        v-if="
                            accessGroup?.type === AccessGroupType.AFFILIATION &&
                            accessGroup?.emailPattern
                        "
                        color="blue-1"
                        text-color="primary"
                        size="sm"
                        class="q-ma-none q-mt-xs"
                    >
                        <div class="row items-center">
                            <q-icon
                                name="sym_o_info"
                                size="16px"
                                class="q-mr-sm"
                            />
                            <span
                                class="text-weight-regular"
                                style="font-size: 13px"
                            >
                                邮箱：
                                <span class="text-weight-bold"
                                    >*@{{ accessGroup.emailPattern }}</span
                                >
                            </span>
                        </div>
                        <q-tooltip
                            class="bg-grey-9 text-body2"
                            :offset="[0, 8]"
                        >
                            Any user logging in with an email ending in
                            <strong>@{{ accessGroup.emailPattern }}</strong> is
                            automatically added to this group.
                        </q-tooltip>
                    </q-chip>
                </div>
            </div>
        </template>
        <template #tabs>
            <q-tabs
                v-model="tab"
                align="left"
                active-color="primary"
                dense
                class="text-grey"
            >
                <q-tab
                    v-if="!personal"
                    name="members"
                    label="成员"
                    style="color: #222"
                />
                <q-tab name="projects" label="项目" style="color: #222" />
            </q-tabs>
        </template>
    </title-section>

    <q-tab-panels v-model="tab" class="q-mt-lg" style="background: transparent">
        <q-tab-panel name="projects">
            <div class="flex justify-between items-center q-mb-lg">
                <div />
                <button-group>
                    <app-search-bar
                        v-model="search"
                        placeholder="搜索"
                        class="q-mr-sm"
                    />
                    <app-refresh-button @click="refetchOnClick" />
                    <app-create-button
                        label="添加项目"
                        @click="openAddProject"
                    />
                </button-group>
            </div>

            <q-table
                ref="tableRef"
                v-model:pagination="pagination"
                v-model:selected="selectedProjects"
                flat
                bordered
                separator="none"
                :rows="projectRows"
                :columns="projectCols as any"
                selection="multiple"
                row-key="uuid"
                :filter="search"
                binary-state-sort
            >
                <template #no-data>
                    <div class="full-width row flex-center q-pa-xl text-grey-8">
                        <div class="text-center">
                            <q-icon
                                name="sym_o_folder_open"
                                size="64px"
                                color="grey-4"
                            />
                            <div class="text-h6 q-mt-md">
                                该组尚未获得任何项目的访问权限。
                            </div>
                            <app-create-button
                                class="q-mt-md"
                                label="分配项目"
                                @click="openAddProject"
                            />
                        </div>
                    </div>
                </template>
                <template #body-selection="props">
                    <q-checkbox
                        v-model="props.selected"
                        color="grey-8"
                        class="checkbox-with-hitbox"
                    />
                </template>
                <template #body-cell-project-action="props">
                    <q-td :props="props">
                        <q-btn
                            flat
                            round
                            dense
                            icon="sym_o_more_vert"
                            unelevated
                            color="primary"
                            class="cursor-pointer"
                            @click.stop
                        >
                            <q-menu auto-close>
                                <q-list>
                                    <q-item
                                        v-ripple
                                        style="width: 180px"
                                        clickable
                                        @click="() => rowClick(props.row.uuid)"
                                    >
                                        <q-item-section>
                                            查看项目详情
                                        </q-item-section>
                                    </q-item>

                                    <change-project-rights-dialog-opener
                                        :project-uuid="props.row.uuid"
                                        :project-access-uuid="
                                            props.row.project_access_uuid
                                        "
                                    >
                                        <q-item v-ripple clickable>
                                            <q-item-section>
                                                更改权限
                                            </q-item-section>
                                        </q-item>
                                    </change-project-rights-dialog-opener>
                                    <RemoveProjectDialogOpener
                                        v-if="accessGroup"
                                        :access-group="accessGroup"
                                        :project-u-u-i-d="props.row.uuid"
                                    >
                                        <q-item v-ripple clickable>
                                            <q-item-section>
                                                移除
                                            </q-item-section>
                                        </q-item>
                                    </RemoveProjectDialogOpener>
                                </q-list>
                            </q-menu>
                        </q-btn>
                    </q-td>
                </template>
            </q-table>
        </q-tab-panel>
        <q-tab-panel v-if="!personal" name="members">
            <div
                v-if="selectedUsers.length === 0"
                class="flex justify-between items-center q-mb-lg"
            >
                <div />
                <button-group>
                    <app-search-bar
                        v-model="search"
                        placeholder="搜索"
                        class="q-mr-sm"
                    />
                    <app-refresh-button @click="refetchOnClick" />

                    <DialogOpenerAddUser
                        v-if="accessGroup"
                        :access-group="accessGroup"
                    >
                        <app-create-button label="添加用户" />
                    </DialogOpenerAddUser>
                </button-group>
            </div>
            <div v-else class="q-py-lg" style="background: #0f62fe">
                <ButtonGroupOverlay>
                    <template #start>
                        <div style="margin: 0; font-size: 14pt; color: white">
                            {{ selectedUsers.length }}
                            个用户已选中
                        </div>
                    </template>
                    <template #end>
                        <q-btn
                            flat
                            dense
                            padding="6px"
                            icon="sym_o_delete"
                            color="white"
                            :disable="!currentUserCanEdit"
                            @click="deleteSelectedUsers"
                        >
                            删除
                            <q-tooltip v-if="!currentUserCanEdit">
                                您无法编辑此组
                            </q-tooltip>
                        </q-btn>
                        <q-btn
                            flat
                            dense
                            padding="6px"
                            icon="sym_o_close"
                            color="white"
                            @click="deselectUsers"
                        />
                    </template>
                </ButtonGroupOverlay>
            </div>
            <q-table
                v-model:pagination="pagination2"
                v-model:selected="selectedUsers"
                :rows="accessGroup?.memberships || []"
                :columns="userCols as any"
                selection="multiple"
                row-key="uuid"
                :filter="search"
                binary-state-sort
                flat
                bordered
            >
                <template #no-data>
                    <div class="full-width row flex-center q-pa-xl text-grey-8">
                        <div class="text-center">
                            <q-icon
                                name="sym_o_group"
                                size="64px"
                                color="grey-4"
                            />
                            <div class="text-h6 q-mt-md">
                                该组还没有成员。
                            </div>
                            <DialogOpenerAddUser
                                v-if="accessGroup"
                                :access-group="accessGroup"
                            >
                                <app-create-button
                                    class="q-mt-md"
                                    label="添加用户"
                                />
                            </DialogOpenerAddUser>
                        </div>
                    </div>
                </template>
                <template #body-selection="props">
                    <q-checkbox
                        v-model="props.selected"
                        color="grey-8"
                        class="checkbox-with-hitbox"
                    />
                </template>
                <template #body-cell-status="props">
                    <q-td :props="props">
                        <app-status-chip
                            :expiration-date="props.row.expirationDate"
                        />
                    </q-td>
                </template>
                <template #body-cell-accessValidUntil="props">
                    <q-td :props="props">
                        <q-btn
                            flat
                            dense
                            no-caps
                            class="button-border"
                            :class="
                                isExpired(props.row.expirationDate)
                                    ? 'text-negative'
                                    : 'text-grey-9'
                            "
                            :disable="!currentUserCanEdit"
                            @click="() => openSetExpirationDialog(props.row)"
                        >
                            <template #default>
                                <div class="row items-center q-px-sm">
                                    <q-icon
                                        size="xs"
                                        name="sym_o_date_range"
                                        class="q-mr-sm"
                                        :color="
                                            isExpired(props.row.expirationDate)
                                                ? 'negative'
                                                : ''
                                        "
                                    />
                                    <span
                                        :class="
                                            isExpired(props.row.expirationDate)
                                                ? 'text-negative text-bold'
                                                : ''
                                        "
                                    >
                                        {{
                                            props.row.expirationDate
                                                ? new Date(
                                                      props.row.expirationDate,
                                                  ).toDateString()
                                                : '永不'
                                        }}
                                    </span>
                                </div>
                            </template>
                        </q-btn>
                    </q-td>
                </template>
                <template #body-cell-actions="props">
                    <q-td :props="props">
                        <q-btn
                            flat
                            round
                            dense
                            icon="sym_o_more_vert"
                            unelevated
                            color="primary"
                            class="cursor-pointer"
                            @click.stop
                        >
                            <q-menu auto-close>
                                <q-list>
                                    <q-item
                                        v-ripple
                                        style="width: 180px"
                                        clickable
                                        disable
                                    >
                                        <q-item-section>
                                            查看详情
                                        </q-item-section>
                                        <q-tooltip>
                                            无法查看用户的详细信息！
                                        </q-tooltip>
                                    </q-item>

                                    <q-item v-ripple clickable disabled>
                                        <q-item-section>编辑</q-item-section>
                                        <q-tooltip>
                                            无法编辑用户！
                                        </q-tooltip>
                                    </q-item>
                                    <q-item
                                        v-ripple
                                        clickable
                                        :disable="!currentUserCanEdit"
                                        @click="
                                            () =>
                                                removeSingleUser(
                                                    props.row.user.uuid,
                                                )
                                        "
                                    >
                                        <q-item-section>移除</q-item-section>
                                    </q-item>
                                </q-list>
                            </q-menu>
                        </q-btn>
                    </q-td>
                </template>
            </q-table>
        </q-tab-panel>
    </q-tab-panels>
</template>
<script setup lang="ts">
import type { GroupMembershipDto } from '@rslstudio/api-dto/types/access-control/group-membership.dto';
import { AccessGroupRights, AccessGroupType } from '@rslstudio/shared';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import DialogOpenerAddUser from 'components/button-wrapper/dialog-opener-add-user.vue';
import ChangeProjectRightsDialogOpener from 'components/button-wrapper/dialog-opener-change-project-rights.vue';
import RemoveProjectDialogOpener from 'components/button-wrapper/remove-project-dialog-opener.vue';
import ButtonGroupOverlay from 'components/buttons/button-group-overlay.vue';
import ButtonGroup from 'components/buttons/button-group.vue';
import AppCreateButton from 'components/common/app-create-button.vue';
import AppRefreshButton from 'components/common/app-refresh-button.vue';
import AppSearchBar from 'components/common/app-search-bar.vue';
import AppStatusChip from 'components/common/app-status-chip.vue';
import TitleSection from 'components/title-section.vue';
import { Notify, QTable, useQuasar } from 'quasar';
import { projectAccessColumns } from 'src/components/explorer-page/explorer-page-table-columns';
import AddProjectToAccessGroupDialog from 'src/dialogs/add-project-access-group-dialog.vue';
import SetAccessGroupExpirationDialog from 'src/dialogs/modify-membership-expiration-date-dialog.vue';
import { useAccessGroup, useUser } from 'src/hooks/query-hooks';
import ROUTES from 'src/router/routes';
import { isExpired } from 'src/services/date-formating';
import {
    removeUsersFromAccessGroup,
    setAccessGroupExpiry,
} from 'src/services/mutations/access';
import { computed, ComputedRef, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

const $q = useQuasar();
const router = useRouter();
const tab = ref('members');
const uuid: ComputedRef<string> = computed(
    () => router.currentRoute.value.params.uuid,
) as ComputedRef<string>;
const selectedProjects = ref([]);
const selectedUsers = ref<GroupMembershipDto[]>([]);

const search = ref('');

const pagination = ref({
    sortBy: 'name',
    descending: false,
    page: 1,
    rowsPerPage: 30,
});

const pagination2 = ref({
    sortBy: 'name',
    descending: false,
    page: 1,
    rowsPerPage: 30,
});

const queryClient = useQueryClient();
const user = useUser();

const refetchOnClick: (event_: Event) => void = () => refetch;

const { data: accessGroup, refetch } = useAccessGroup(uuid.value);

const { mutate: removeUsers } = useMutation({
    mutationFn: (userUuids: string[]) =>
        removeUsersFromAccessGroup(userUuids, uuid.value),
    onSuccess: async () => {
        selectedUsers.value = [];
        await queryClient.invalidateQueries({
            queryKey: ['AccessGroup', uuid.value],
        });
        Notify.create({
            message: '用户已成功移除',
            color: 'positive',
            position: 'bottom',
        });
    },
    onError: () => {
        Notify.create({
            message: '从权限组移除用户时出错',
            color: 'negative',
            position: 'bottom',
        });
    },
});

const removeSingleUser = (userUuid: string): void => {
    removeUsers([userUuid]);
};

const deleteSelectedUsers = (): void => {
    if (selectedUsers.value.length > 0) {
        removeUsers(selectedUsers.value.map((m) => m.user.uuid));
    }
};

const deselectUsers = (): void => {
    selectedUsers.value = [];
};

const personal = computed(
    () => accessGroup.value?.type === AccessGroupType.PRIMARY,
);

watch(
    () => personal.value,
    (value) => {
        if (value) {
            tab.value = 'projects';
        }
    },
    { immediate: true },
);

const projectRows = computed(() => {
    return accessGroup.value?.projectAccesses ?? [];
});

const openAddProject = (): void => {
    $q.dialog({
        component: AddProjectToAccessGroupDialog,
        componentProps: {
            accessGroupUuid: uuid.value,
        },
    });
};

const renameColumns = (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    cols: any[],
    oldLabel: string,
    newLabel: string,
): void => {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    for (const col of cols.filter((c) => c.label === oldLabel)) {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
        col.label = newLabel;
    }
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const dropColumns = (cols: any[], label: string) => {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return
    return cols.filter((col) => col.label !== label);
};

const { mutate: setAccessGroup } = useMutation({
    mutationFn: (data: {
        uuid: string;
        userUuid: string;
        expirationDate: Date | null;
    }) => {
        return setAccessGroupExpiry(
            data.uuid,
            data.userUuid,
            data.expirationDate,
        );
    },
    onSuccess: async () => {
        await queryClient.invalidateQueries({
            predicate: (query) => {
                return (
                    query.queryKey[0] === 'AccessGroup' &&
                    query.queryKey[1] === uuid.value
                );
            },
        });
        Notify.create({
            message: '过期日期已设置',
            color: 'positive',
            position: 'bottom',
        });
    },
    onError: () => {
        Notify.create({
            message: '设置过期日期时出错',
            color: 'negative',
            position: 'bottom',
        });
    },
});

const openSetExpirationDialog = (agu: GroupMembershipDto): void => {
    $q.dialog({
        component: SetAccessGroupExpirationDialog,
        componentProps: {
            agu: agu,
        },
    }).onOk((expirationDate: Date | null) => {
        setAccessGroup({
            uuid: accessGroup.value?.uuid ?? '',
            userUuid: agu.user.uuid,
            expirationDate,
        });
    });
};

const projectCols = computed(() => {
    {
        let defaultCols = [...projectAccessColumns];
        renameColumns(defaultCols, 'Creator', '项目创建者');
        renameColumns(defaultCols, 'Description', '项目描述');
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        defaultCols = dropColumns(defaultCols, 'Created');

        // add as the second to last column
        defaultCols.splice(-2, 1, {
            name: 'rights',
            required: true,
            label: '组权限',
            style: 'max-width: 100px',
            align: 'left',
            // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access
            field: (row: any) => AccessGroupRights[row.rights],
        });
        return defaultCols;
    }
});

const currentUserCanEdit = computed(() => {
    return (
        accessGroup.value?.memberships.some(
            (m) => m.user.uuid === user.data.value?.uuid && m.canEditGroup,
        ) ?? false
    );
});

const userCols = [
    {
        name: 'name',
        required: true,
        label: '名称',
        align: 'left',
        field: (row: GroupMembershipDto): string => row.user.name,
        format: (value: string): string => value,
        style: 'width: 10%',
    },
    {
        name: 'email',
        required: false,
        label: '邮箱',
        align: 'left',
        field: (row: GroupMembershipDto): string => row.user.email ?? 'N/A',
        format: (value: string): string => value,
        style: 'width: 20%; color: #666',
    },
    {
        name: 'status',
        required: true,
        label: '状态',
        align: 'left',
    },
    {
        name: 'accessValidUntil',
        required: true,
        label: '权限有效期至',
        align: 'left',
    },
    {
        name: 'role',
        required: true,
        label: '角色',
        align: 'left',
        field: (row: GroupMembershipDto): string =>
            row.canEditGroup ? '所有者' : '成员',
    },
    {
        name: 'actions',
        required: true,
        label: '',
        align: 'center',
        field: 'actions',
        style: 'width: 5%',
    },
];

const rowClick = async (_uuid: string): Promise<void> => {
    await router.push({
        name: ROUTES.MISSIONS.routeName,
        params: {
            projectUuid: _uuid,
        },
    });
};
</script>
<style scoped></style>
