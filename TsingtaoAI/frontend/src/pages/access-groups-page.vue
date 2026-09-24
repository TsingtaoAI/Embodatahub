<template>
    <title-section title="权限控制">
        <template #tabs>
            <q-tabs
                v-model="tab"
                align="left"
                active-color="primary"
                dense
                class="text-grey"
            >
                <q-tab name="users" label="用户" style="color: #222" />
                <q-tab name="groups" label="用户组" style="color: #222" />
            </q-tabs>
        </template>
    </title-section>

    <div class="q-my-lg">
        <div class="flex justify-between items-center">
            <button-group>
                <div
                    v-if="tab === 'groups'"
                    class="self-stretch flex items-center"
                >
                    <q-btn-toggle
                        v-model="prefilter"
                        :options="prefilterOptions"
                        unelevated
                        no-caps
                        toggle-color="grey-10"
                        toggle-text-color="white"
                        color="white"
                        text-color="grey-7"
                        style="border: 1px solid #e0e0e0; border-radius: 4px"
                        @update:model-value="updatePrefilter"
                    />
                </div>
            </button-group>

            <button-group>
                <app-search-bar
                    v-model="filterOptions.search"
                    :placeholder="
                        tab === 'groups' ? '搜索用户组' : '搜索用户'
                    "
                />

                <app-refresh-button @click="refetchAccessGroup" />

                <CreateAccessGroupDialogOpener v-if="tab === 'groups'" />
            </button-group>
        </div>

        <div
            v-if="selectedAccessGroups.length > 0"
            class="q-py-lg"
            style="background: #0f62fe; margin-top: 24px"
        >
            <ButtonGroupOverlay>
                <template #start>
                    <div style="margin: 0; font-size: 14pt; color: white">
                        {{ selectedAccessGroups.length }} 个已选中
                    </div>
                </template>
                <template #end>
                    <!-- TODO: bulk actions -->
                    <q-btn
                        flat
                        dense
                        padding="6px"
                        icon="sym_o_close"
                        color="white"
                        @click="deselectAccessGroups"
                    />
                </template>
            </ButtonGroupOverlay>
        </div>

        <q-table
            v-model:pagination="pagination"
            v-model:selected="selectedAccessGroups"
            flat
            bordered
            wrap-cells
            virtual-scroll
            separator="none"
            :rows="accessGroupsTable"
            :columns="activeColumns as any"
            style="margin-top: 24px"
            selection="multiple"
            row-key="uuid"
            @row-click="rowClick"
        >
            <template #body-selection="props">
                <q-checkbox
                    v-model="props.selected"
                    color="grey-8"
                    class="checkbox-with-hitbox"
                />
            </template>
            <template #body-cell-Status="props">
                <q-td :props="props">
                    <app-status-chip
                        :expiration-date="
                            props.row.memberships[0]?.expirationDate
                        "
                    />
                </q-td>
            </template>
            <template #body-cell-accessgroupaction="props">
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
                                    clickable
                                    @click="
                                        () => rowClick(undefined, props.row)
                                    "
                                >
                                    <q-item-section>
                                        查看详情
                                    </q-item-section>
                                </q-item>

                                <q-item v-ripple clickable disabled>
                                    <q-tooltip
                                        v-if="
                                            filterOptions.type ===
                                            AccessGroupType.PRIMARY
                                        "
                                    >
                                        无法编辑个人权限组
                                    </q-tooltip>
                                    <q-item-section>编辑</q-item-section>
                                </q-item>
                                <DeleteAccessGroup :access-group="props.row">
                                    <q-item v-ripple clickable>
                                        <q-item-section>删除</q-item-section>
                                    </q-item>
                                </DeleteAccessGroup>
                            </q-list>
                        </q-menu>
                    </q-btn>
                </q-td>
            </template>
        </q-table>
    </div>
</template>
<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query';

import { formatDate, isExpired } from 'src/services/date-formating';
import { computed, Ref, ref, watch } from 'vue';

import type { AccessGroupDto } from '@rslstudio/api-dto/types/access-control/access-group.dto';
import type { AccessGroupsDto } from '@rslstudio/api-dto/types/access-control/access-groups.dto';
import type { ProjectWithMissionsDto } from '@rslstudio/api-dto/types/project/project-with-missions.dto';
import { AccessGroupType } from '@rslstudio/shared';
import DeleteAccessGroup from 'components/button-wrapper/delete-access-group.vue';
import CreateAccessGroupDialogOpener from 'components/button-wrapper/dialog-opener-create-access-group.vue';
import ButtonGroupOverlay from 'components/buttons/button-group-overlay.vue';
import ButtonGroup from 'components/buttons/button-group.vue';
import AppRefreshButton from 'components/common/app-refresh-button.vue';
import AppSearchBar from 'components/common/app-search-bar.vue';
import AppStatusChip from 'components/common/app-status-chip.vue';
import TitleSection from 'components/title-section.vue';
import { QTable } from 'quasar';
import ROUTES from 'src/router/routes';
import { searchAccessGroups } from 'src/services/queries/access';
import { useRoute, useRouter } from 'vue-router';

const $router = useRouter();
const route = useRoute();
const tab = ref((route.query.tab as string) || 'groups');

const prefilterOptions = [
    { label: '自定义组', value: AccessGroupType.CUSTOM },
    { label: '归属组', value: AccessGroupType.AFFILIATION },
];
const prefilter = ref<AccessGroupType>(AccessGroupType.CUSTOM);

const selectedAccessGroups: Ref<ProjectWithMissionsDto[]> = ref([]);

function deselectAccessGroups() {
    selectedAccessGroups.value = [];
}

const filterOptions: Ref<{
    type: AccessGroupType;
    search: string;
    creator: boolean;
    member: boolean;
}> = ref({
    type: AccessGroupType.CUSTOM,
    search: '',
    creator: false,
    member: false,
});

watch(
    () => tab.value,
    (newTab) => {
        selectedAccessGroups.value = [];
        void $router.replace({ query: { ...route.query, tab: newTab } });
        if (newTab === 'users') {
            filterOptions.value.type = AccessGroupType.PRIMARY;
            filterOptions.value.creator = false;
            filterOptions.value.member = false;
        } else {
            applyPrefilter(prefilter.value);
        }
    },
    { immediate: true },
);

watch(
    () => prefilter.value,
    (newValue) => {
        if (tab.value === 'groups') {
            applyPrefilter(newValue);
        }
    },
);

function applyPrefilter(value: AccessGroupType | undefined) {
    if (!value) return;
    if (value === AccessGroupType.CUSTOM) {
        filterOptions.value.type = AccessGroupType.CUSTOM;
        filterOptions.value.creator = false;
        filterOptions.value.member = false;
    } else if (value === AccessGroupType.AFFILIATION) {
        filterOptions.value.type = AccessGroupType.AFFILIATION;
        filterOptions.value.creator = true;
        filterOptions.value.member = false;
    }
}

function updatePrefilter(value: string | string[]) {
    if (typeof value === 'string') {
        prefilter.value = value as AccessGroupType;
    }
}

const pagination = ref({
    sortBy: 'name',
    descending: false,
    page: 1,
    rowsPerPage: 30,
});
const accessGroupKey = computed(() => [
    'accessGroups',
    filterOptions.value,
    pagination.value,
]);

const { data: foundAccessGroups, refetch } = useQuery<AccessGroupsDto>({
    queryKey: accessGroupKey,
    queryFn: () =>
        searchAccessGroups(
            filterOptions.value.search,
            filterOptions.value.type,
            (pagination.value.page - 1) * pagination.value.rowsPerPage,
            pagination.value.rowsPerPage,
        ),
});

const refetchAccessGroup: (event_: Event) => Promise<void> = async () => {
    await refetch();
};

const accessGroupsTable = computed(() =>
    foundAccessGroups.value ? foundAccessGroups.value.data : [],
);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function rowClick(event: any, row: AccessGroupDto) {
    await $router.push({
        name: ROUTES.ACCESS_GROUP.routeName,
        params: { uuid: row.uuid },
    });
}

const usersColumns = [
    {
        name: 'Name',
        required: true,
        label: '名称',
        align: 'left',
        field: (row: AccessGroupDto): string => row.name,
        format: (value: string): string => value,
        sortable: true,
        style: 'width:  20%; max-width: 60%; min-width: 10%;',
    },
    {
        name: 'Email',
        required: false,
        label: '邮箱',
        align: 'left',
        field: (row: AccessGroupDto): string =>
            row.memberships[0]?.user.email ?? '-',
        format: (value: string): string => value,
        sortable: false,
    },
    {
        name: 'Status',
        required: true,
        label: '状态',
        align: 'center',
        field: (row: AccessGroupDto): string => {
            const exp = row.memberships[0]?.expirationDate;
            if (isExpired(exp)) {
                return '已过期';
            }
            return '活跃';
        },
        format: (value: string): string => value,
        sortable: true,
        style: 'width:  10%; max-width: 10%; min-width: 10%;',
    },
    {
        name: 'Projects',
        required: true,
        label: '项目数',
        align: 'center',
        field: (row: AccessGroupDto): string =>
            row.projectAccesses.length.toString(),
        format: (value: string): string => value,
        sortable: true,
        style: 'width:  10%; max-width: 10%; min-width: 5%;',
    },
    {
        name: 'accessgroupaction',
        label: ' ',
        align: 'center',
        style: 'width:  2%; max-width: 10%; min-width: 2%;',
    },
];

const accessGroupsColumns = [
    {
        name: 'Access Group',
        required: true,
        label: '组名称',
        align: 'left',
        field: (row: AccessGroupDto): string => row.name,
        format: (value: string): string => value,
        sortable: true,
        style: 'width:  20%; max-width: 60%; min-width: 10%;',
    },
    {
        name: 'Creator',
        required: false,
        label: '创建者',
        align: 'center',
        field: (row: AccessGroupDto): string => row.creator?.name ?? '-',
        format: (value: string): string => value,
        sortable: false,
    },
    {
        name: 'createdAt',
        required: true,
        label: '创建日期',
        align: 'center',
        field: (row: AccessGroupDto): string =>
            row.createdAt.toLocaleDateString(),
        format: (value: string): string => formatDate(new Date(value)),
        sortable: true,
        style: 'width:  10%; max-width: 10%; min-width: 10%;',
    },
    {
        name: 'NrOfUsers',
        required: true,
        label: '成员数',
        align: 'center',
        field: (row: AccessGroupDto): string =>
            row.memberships.length.toString(),
        format: (value: string): string => value,
        sortable: true,
        style: 'width:  10%; max-width: 10%; min-width: 5%;',
    },
    {
        name: 'NrOfProjects',
        required: true,
        label: '项目数',
        align: 'center',
        field: (row: AccessGroupDto): string =>
            row.projectAccesses.length.toString(),
        format: (value: string): string => value,
        sortable: true,
        style: 'width:  10%; max-width: 10%; min-width: 5%;',
    },
    {
        name: 'accessgroupaction',
        label: ' ',
        align: 'center',
        style: 'width:  2%; max-width: 10%; min-width: 2%;',
    },
];

const activeColumns = computed(() => {
    return tab.value === 'users' ? usersColumns : accessGroupsColumns;
});
</script>

<style scoped></style>
