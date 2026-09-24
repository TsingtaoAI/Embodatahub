<template>
    <base-dialog ref="dialogRef">
        <template #title> 删除文件 </template>
        <template #content>
            <q-card-section class="q-pa-md">
                <p>
                    请输入文件名确认：
                    <b>{{ filename }}</b>
                </p>
                <q-input
                    v-model="fileNameCheck"
                    outlined
                    placeholder="确认文件名"
                    autofocus
                />
            </q-card-section>
        </template>

        <template #actions>
            <q-btn
                flat
                :disable="fileNameCheck !== filename"
                label="删除文件"
                class="bg-button-danger"
                @click="onDialogOK"
            />
        </template>
    </base-dialog>
</template>
<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import BaseDialog from 'src/dialogs/base-dialog.vue';
import { ref } from 'vue';

const { dialogRef, onDialogOK } = useDialogPluginComponent();
const fileNameCheck = ref('');

defineProps<{
    filename: string;
}>();
</script>
