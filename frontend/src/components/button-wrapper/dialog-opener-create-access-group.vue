<template>
    <app-create-button
        label="创建访问组"
        :disable="!canCreate"
        @click="createAccessGroupDialog"
    >
        <q-tooltip v-if="!canCreate">
            您没有权限创建新的访问组
        </q-tooltip>
    </app-create-button>
</template>

<script setup lang="ts">
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import AppCreateButton from 'components/common/app-create-button.vue';
import { Notify, useQuasar } from 'quasar';
import CreateAccessGroupDialog from 'src/dialogs/create-access-group-dialog.vue';
import { canCreateProject, usePermissionsQuery } from 'src/hooks/query-hooks';
import { createAccessGroup } from 'src/services/mutations/access';
import { computed, unref } from 'vue';

const { data: permissions } = usePermissionsQuery();
const canCreate = computed(() => canCreateProject(permissions.value));
const queryClient = useQueryClient();

const $q = useQuasar();

const { mutate: _createAccessGroup } = useMutation({
    mutationFn: (name: string) => createAccessGroup(unref(name)),
    onSuccess: async () => {
        await queryClient.invalidateQueries({
            predicate: (query) => {
                return query.queryKey[0] === 'accessGroups';
            },
        });
        Notify.create({
            message: '访问组创建成功',
            color: 'positive',
            position: 'bottom',
            timeout: 2000,
        });
    },
    onError: () => {
        Notify.create({
            message: '创建访问组失败',
            color: 'negative',
            position: 'bottom',
            timeout: 2000,
        });
    },
});

const createAccessGroupDialog = (): void => {
    $q.dialog({
        component: CreateAccessGroupDialog,
    }).onOk((name: string) => {
        _createAccessGroup(name);
    });
};
</script>
