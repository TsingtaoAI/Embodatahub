<template>
    <base-dialog ref="dialogRef">
        <template #title> 添加分类 </template>
        <template #tabs>
            <q-tabs
                v-model="tab"
                dense
                class="text-grey"
                align="left"
                active-color="primary"
            >
                <q-tab name="add" label="添加" style="color: #222" />
                <q-tab
                    name="create"
                    label="创建分类"
                    style="color: #222"
                />
            </q-tabs>
        </template>
        <template #content>
            <q-tab-panels v-model="tab">
                <q-tab-panel name="add" style="min-height: 180px">
                    <label for="categoryName">选择分类</label>
                    <category-selector
                        :selected="selected"
                        :project-uuid="projectUuid"
                        @update:selected="updateSelected"
                    />
                </q-tab-panel>
                <q-tab-panel name="create" style="min-height: 180px">
                    <CategoryCreator :project-uuid="projectUuid" />
                </q-tab-panel>
            </q-tab-panels>
        </template>
        <template #actions>
            <q-btn
                label="保存"
                class="bg-button-primary"
                :disable="selected.length === 0"
                @click="addCategories"
            />
        </template>
    </base-dialog>
</template>
<script setup lang="ts">
import type { CategoryDto } from '@rslstudio/api-dto/types/category.dto';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { Notify, useDialogPluginComponent } from 'quasar';
import BaseDialog from 'src/dialogs/base-dialog.vue';
import { addManyCategories } from 'src/services/mutations/categories';
import { Ref, ref } from 'vue';

import type { FileWithTopicDto } from '@rslstudio/api-dto/types/file/file.dto';
import CategoryCreator from 'components/category-creator.vue';
import CategorySelector from 'components/category-selector.vue';

const { dialogRef, onDialogOK } = useDialogPluginComponent();

const { missionUuid, projectUuid, files } = defineProps<{
    missionUuid: string;
    projectUuid: string;
    files: FileWithTopicDto[];
}>();
const queryClient = useQueryClient();
const selected: Ref<CategoryDto[]> = ref<CategoryDto[]>([]);

const tab = ref('add');

const updateSelected = (value: CategoryDto[]): void => {
    selected.value = value;
};

const { mutate } = useMutation({
    mutationFn: async () => {
        await addManyCategories(
            missionUuid,
            files.map((f) => f.uuid),
            selected.value.map((c) => c.uuid),
        );
        onDialogOK();
    },
    onSuccess: async () => {
        Notify.create({
            message: '分类已添加',
            color: 'positive',
            position: 'bottom',
        });
        await queryClient.invalidateQueries({
            queryKey: ['files'],
        });
    },
    onError: (error: Error) => {
        Notify.create({
            message: error.message,
            color: 'negative',
            position: 'bottom',
        });
    },
});

const addCategories = (): void => {
    mutate();
};
</script>
<style scoped></style>
