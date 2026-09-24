<template>
    <base-dialog ref="dialogRef">
        <template #title> 创建访问组 </template>

        <template #content>
            <label for="name" class="text-weight-bold">
                组名<span class="text-negative">*</span>
            </label>
            <q-input
                v-model="name"
                placeholder="名称..."
                name="name"
                :error-message="errorMessagesProjectName"
                :error="isInErrorStateProjectName"
                outlined
                dense
                autofocus
            />
        </template>

        <template #actions>
            <q-btn
                flat
                label="创建访问组"
                class="bg-button-primary"
                :disable="isInErrorStateProjectName"
                @click="createAccessGroup"
            />
        </template>
    </base-dialog>
</template>
<script setup lang="ts">
import { QInput, useDialogPluginComponent } from 'quasar';
import BaseDialog from 'src/dialogs/base-dialog.vue';
import { ref, watch } from 'vue';

const { dialogRef, onDialogOK } = useDialogPluginComponent();
const isInErrorStateProjectName = ref(false);
const errorMessagesProjectName = ref<string>();
const name = ref('');

watch(name, () => {
    if (/^[\w\-_]{3,20}$/.test(name.value)) {
        isInErrorStateProjectName.value = false;
        errorMessagesProjectName.value = '';
    } else {
        isInErrorStateProjectName.value = true;
        errorMessagesProjectName.value =
            '名称长度需为3-20个字符，只能包含字母、数字、- 和 _';
    }
});

const createAccessGroup = (): void => {
    onDialogOK(name);
};
</script>

<style scoped></style>
