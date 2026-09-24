<template>
    <base-dialog ref="dialogRef">
        <template #title> 添加元数据</template>

        <template #content>
            <AddTag :mission-uuid="missionUuid" />
        </template>

        <template #actions>
            <q-btn
                flat
                label="添加元数据"
                class="bg-button-primary"
                @click="onDialogOK"
            />
        </template>
    </base-dialog>
    >
</template>

<script setup lang="ts">
import AddTag from 'components/AddTag.vue';
import { useDialogPluginComponent } from 'quasar';
import BaseDialog from 'src/dialogs/base-dialog.vue';

const { dialogRef, onDialogOK } = useDialogPluginComponent();

const { missionUuid } = defineProps<{
    missionUuid: string;
}>();
</script>

<style scoped></style>
