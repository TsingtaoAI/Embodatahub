<template>
    <div>
        <div class="q-pa-md">
            <div class="text-h5 q-mb-md">
                {{ project?.name ?? $t('project.datasets') }}
            </div>
            <div class="text-grey-7 q-mb-lg">
                {{ project?.description ?? '' }}
            </div>

            <q-btn
                color="primary"
                icon="sym_o_add"
                :label="$t('project.importDataset')"
                class="q-mb-md"
                @click="navigateToRdsImport"
            />

            <!-- Loading -->
            <div v-if="loading" class="text-center q-py-xl">
                <q-spinner size="48px" color="primary" />
                <div class="text-grey-7 q-mt-md">{{ $t('common.loading') }}</div>
            </div>

            <!-- Error -->
            <div v-else-if="error" class="text-center q-py-xl">
                <q-icon name="sym_o_error" size="48px" color="negative" />
                <div class="text-negative q-mt-md">{{ error }}</div>
            </div>

            <!-- Empty -->
            <div v-else-if="datasets.length === 0" class="text-center q-py-xl">
                <q-icon name="sym_o_folder_off" size="64px" color="grey-6" />
                <div class="text-h6 text-grey-7 q-mt-md">{{ $t('project.noDatasets') }}</div>
                <p class="text-grey-6">{{ $t('project.noDatasetsHint') }}</p>
            </div>

            <!-- Table -->
            <q-table
                v-else
                :rows="datasets"
                :columns="columns"
                row-key="uuid"
                flat
                bordered
            >
                <template #body-cell-format="props">
                    <q-td :props="props">
                        <q-badge color="primary" :label="props.row.format" outline />
                    </q-td>
                </template>
                <template #body-cell-qualityStatus="props">
                    <q-td :props="props">
                        <span v-if="props.row.passedCount > 0" class="q-mr-sm" style="color:#2e7d32">
                            {{ $t('project.passed') }} {{ props.row.passedCount }}
                        </span>
                        <span v-if="props.row.reviewCount > 0" class="q-mr-sm" style="color:#e65100">
                            {{ $t('project.review') }} {{ props.row.reviewCount }}
                        </span>
                        <span v-if="props.row.excludedCount > 0" class="q-mr-sm" style="color:#c62828">
                            {{ $t('project.excluded') }} {{ props.row.excludedCount }}
                        </span>
                        <span
                            v-if="!props.row.passedCount && !props.row.reviewCount && !props.row.excludedCount"
                            class="text-grey-6"
                        >{{ $t('project.unprocessed') }}</span>
                    </q-td>
                </template>
            </q-table>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useProjectUUID } from 'src/hooks/router-hooks';
import { getProject } from 'src/services/queries/project';
import { getDatasetsByProject } from 'src/services/queries/rds';
import type { RdsDatasetSummaryDto } from '@rslstudio/api-dto/types/rds/rds-dataset.dto';
import type { ProjectWithRequiredTagsDto } from '@rslstudio/api-dto/types/project/project-with-required-tags.dto';

const $router = useRouter();
const { t } = useI18n();
const projectUuid = useProjectUUID();

const project = ref<ProjectWithRequiredTagsDto | null>(null);
const datasets = ref<RdsDatasetSummaryDto[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const columns = computed(() => [
    { name: 'name', label: t('project.datasetName'), field: 'name', align: 'left' as const, sortable: true },
    { name: 'format', label: t('project.format'), field: 'format', align: 'left' as const, sortable: true },
    { name: 'totalEpisodes', label: t('project.episodes'), field: 'totalEpisodes', align: 'center' as const, sortable: true },
    {
        name: 'totalFrames',
        label: t('project.totalFrames'),
        field: (row: RdsDatasetSummaryDto) => row.totalFrames.toLocaleString(),
        align: 'right' as const,
        sortable: true,
    },
    { name: 'fps', label: t('project.frameRate'), field: 'fps', align: 'center' as const, sortable: true, format: (val: number) => `${val} Hz` },
    { name: 'qualityStatus', label: t('project.qualityStatus'), field: 'passedCount', align: 'left' as const, sortable: true },
]);

async function loadData() {
    if (!projectUuid.value) {
        error.value = t('errors.projectUuidNotFound');
        loading.value = false;
        return;
    }
    try {
        loading.value = true;
        error.value = null;
        const [projectData, datasetsData] = await Promise.all([
            getProject(projectUuid.value),
            getDatasetsByProject(projectUuid.value),
        ]);
        project.value = projectData;
        datasets.value = datasetsData;
    } catch (e) {
        error.value = e instanceof Error ? e.message : t('errors.loadDatasetsFailed');
    } finally {
        loading.value = false;
    }
}

function navigateToRdsImport() {
    const params = new URLSearchParams();
    params.set('page', 'import');
    if (projectUuid.value) params.set('projectUuid', projectUuid.value);
    if (project.value?.name) params.set('projectName', project.value.name);
    void $router.push(`/robot-data-studio/import?${params.toString()}`);
}

onMounted(() => {
    void loadData();
});
</script>
