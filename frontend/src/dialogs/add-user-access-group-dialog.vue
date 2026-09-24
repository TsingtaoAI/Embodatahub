<template>
    <base-dialog ref="dialogRef">
        <template #title>将用户添加到访问组</template>

        <template #content>
            <AddUserToAccessGroup
                ref="addUserReference"
                :access-group-uuid="accessGroupUuid"
            />
        </template>

        <template #actions>
            <q-btn
                flat
                label="确认"
                class="bg-button-primary"
                @click="addUserToAccessGroupAction"
            />
        </template>
    </base-dialog>
</template>
<script setup lang="ts">
import AddUserToAccessGroup from 'components/add-user-access-group.vue';
import { useDialogPluginComponent } from 'quasar';
import BaseDialog from 'src/dialogs/base-dialog.vue';
import { ref } from 'vue';

const { dialogRef, onDialogOK } = useDialogPluginComponent();
const addUserReference = ref<InstanceType<typeof AddUserToAccessGroup> | null>(
    // TODO: check why we need null as a value

    null,
);

const { accessGroupUuid } = defineProps<{
    accessGroupUuid: string;
}>();

const addUserToAccessGroupAction = (): void => {
    if (addUserReference.value) {
        addUserReference.value.mutate?.();
    }
    onDialogOK();
};
</script>

<style scoped></style>
