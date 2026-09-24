<template>
    <BaseDialog ref="dialogRef">
        <template #title> 新建项目</template>

        <template #tabs>
            <q-tabs
                v-model="tab"
                dense
                class="text-grey"
                align="left"
                active-color="primary"
            >
                <q-tab
                    name="meta_data"
                    label="项目详情*"
                    style="color: #222"
                />
                <q-tab
                    name="tags"
                    label="任务元数据"
                    style="color: #222"
                    :disable="!formIsValid"
                />
                <q-tab
                    name="manage_access"
                    label="管理权限"
                    style="color: #222"
                    :disable="!formIsValid"
                />
            </q-tabs>
        </template>

        <template #content>
            <q-tab-panels v-model="tab">
                <q-tab-panel name="meta_data" style="min-height: 280px">
                    <label for="projectName">项目名称 *</label>
                    <q-input
                        ref="projectNameInput"
                        v-model="newProjectName"
                        name="projectName"
                        outlined
                        autofocus
                        dense
                        placeholder="名称..."
                        style="padding-bottom: 30px"
                        :error-message="errorMessagesProjectName"
                        :error="isInErrorStateProjectName"
                        :rules="[
                            (val) => !!val || '此项必填',
                            (val) =>
                                val.length >= 3 ||
                                '名称至少3个字符',
                            (val) =>
                                val.length <= 20 ||
                                '名称最多20个字符',
                            (val) =>
                                /^[\w\-_]+$/g.test(val) ||
                                '名称只能包含字母、数字、- 和 _',
                        ]"
                        @update:model-value="verifyInput"
                    />

                    <label for="projectDescription"
                        >项目描述 *</label
                    >
                    <q-input
                        v-model="newProjectDescription"
                        name="projectDescription"
                        type="textarea"
                        outlined
                        dense
                        placeholder="描述..."
                        aria-placeholder="项目名称"
                        style="padding-bottom: 10px"
                        :error-message="errorMessagesProjectDescr"
                        :error="isInErrorStateProjectDescr"
                        autofocus
                        @update:model-value="verifyInput"
                    />
                </q-tab-panel>

                <q-tab-panel name="tags">
                    <ConfigureMetadata v-model:selected="selected" />
                </q-tab-panel>

                <q-tab-panel name="manage_access">
                    <access-rights-manager
                        v-model="accessGroups"
                        :min-access-rights="minAccessRights"
                    />
                </q-tab-panel>
            </q-tab-panels>
        </template>
        <template v-if="tab === 'manage_access'" #actions>
            <q-btn
                flat
                label="创建项目"
                class="bg-button-primary"
                :disable="!formIsValid"
                @click="submitNewProject"
            />
        </template>
        <template v-else #actions>
            <q-btn
                flat
                label="下一步"
                class="bg-button-primary"
                :disable="!formIsValid"
                @click="nextTab"
            />
        </template>
    </BaseDialog>
</template>

<script setup lang="ts">
import BaseDialog from 'src/dialogs/base-dialog.vue';

import type { DefaultRightDto } from '@rslstudio/api-dto/types/access-control/default-right.dto';
import type { TagTypeDto } from '@rslstudio/api-dto/types/tags/tags.dto';
import { AccessGroupType } from '@rslstudio/shared';
import { useQueryClient } from '@tanstack/vue-query';
import AccessRightsManager from 'components/configure-access-rights/access-rights-manager.vue';
import ConfigureMetadata from 'components/configure-metadata.vue';
import { QInput, useDialogPluginComponent, useQuasar } from 'quasar';
import { useProjectDefaultAccess } from 'src/hooks/query-hooks';
import { createProject } from 'src/services/mutations/project';
import { computed, Ref, ref, watch } from 'vue';

const formIsValid = ref(false);
const isInErrorStateProjectName = ref(false);
const errorMessagesProjectName = ref<string>();
const isInErrorStateProjectDescr = ref(false);
const errorMessagesProjectDescr = ref<string>();

const { dialogRef, onDialogOK } = useDialogPluginComponent();
const queryClient = useQueryClient();

const projectNameInput = ref<QInput>();
const newProjectName = ref('');
const newProjectDescription = ref('');
const invalidProjectNames = ref<string[]>([]);

const tab = ref('meta_data');

const selected: Ref<TagTypeDto[]> = ref([]);
const $q = useQuasar();

const { data: defaultRights } = useProjectDefaultAccess();

const minAccessRights = computed(() =>
    defaultRights.value
        ? defaultRights.value.data.filter(
              (r) => r.type === AccessGroupType.PRIMARY,
          )
        : [],
);

const accessGroups = ref<DefaultRightDto[]>(defaultRights.value?.data ?? []);
watch(defaultRights, () => {
    accessGroups.value = defaultRights.value?.data ?? [];
});

const verifyInput = () => {
    formIsValid.value =
        !!newProjectName.value &&
        !!newProjectDescription.value &&
        !invalidProjectNames.value.includes(newProjectName.value) &&
        !!newProjectName.value &&
        !!newProjectDescription.value;

    // client side verification
    if (
        !newProjectName.value ||
        invalidProjectNames.value.includes(newProjectName.value)
    ) {
        isInErrorStateProjectName.value = true;
        errorMessagesProjectName.value = '项目名称不能为空';
    } else {
        isInErrorStateProjectName.value = false;
        errorMessagesProjectName.value = '';
    }

    if (newProjectDescription.value) {
        isInErrorStateProjectDescr.value = false;
        errorMessagesProjectDescr.value = '';
    } else {
        isInErrorStateProjectDescr.value = true;
        errorMessagesProjectDescr.value = '项目描述不能为空';
    }
};

const nextTab = () => {
    if (tab.value === 'meta_data') {
        tab.value = 'tags';
    } else if (tab.value === 'tags') {
        tab.value = 'manage_access';
    }
};

const submitNewProject = async () => {
    await createProject(
        newProjectName.value,
        newProjectDescription.value,
        selected.value.map((tag) => tag.uuid),
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        accessGroups.value.map((r) => ({
            accessGroupUUID: r.uuid,
            rights: r.rights,
        })) || [],
        // @ts-ignore
        defaultRights.value?.data
            .filter((r) => !accessGroups.value.some((a) => a.uuid === r.uuid))
            .map((r) => r.uuid),
    )
        .then(async () => {
            await queryClient.invalidateQueries({ queryKey: ['projects'] });
            await queryClient.invalidateQueries({ queryKey: ['permissions'] });

            $q.notify({
                message: '项目创建成功',
                color: 'positive',
                position: 'bottom',
                timeout: 2000,
            });

            onDialogOK();
        })
        .catch((error: unknown) => {
            // @ts-ignore
            if (error.code === 'ERR_BAD_REQUEST') {
                isInErrorStateProjectName.value = true;
                // @ts-ignore
                errorMessagesProjectName.value = (
                    error as {
                        response?: { data?: { message?: string } };
                    }
                ).response?.data.message;
                invalidProjectNames.value.push(newProjectName.value);
            }

            isInErrorStateProjectName.value = true;
            // @ts-ignore
            errorMessagesProjectName.value = (
                error as {
                    response?: { data?: { message?: string } };
                }
            ).response?.data.message;

            // abort the close of the dialog
            dialogRef.value?.show();
            tab.value = 'meta_data';
        });
};
</script>
