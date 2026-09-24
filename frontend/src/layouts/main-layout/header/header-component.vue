<template>
    <q-header class="bg-default text-grey-8 q-px-lg">
        <q-toolbar class="q-pa-none height-xxl">
            <q-toolbar-title
                shrink
                class="q-pa-none"
                @click="navigateBackToHome"
            >
                <rslstudio-logo class="q-pr-lg" />
            </q-toolbar-title>

            <q-separator vertical />

            <header-tabs :main-menu="mainMenu" class="q-ml-lg" />

            <q-space />

            <Suspense>
                <header-right-menu />
            </Suspense>
        </q-toolbar>
        <bread-crumbs-navigation />
    </q-header>
</template>

<script setup lang="ts">
import RslStudioLogo from 'src/components/images/rslstudio-logo.vue';
import ROUTES from 'src/router/routes';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { computed } from 'vue';
import BreadCrumbsNavigation from './bread-crumb-navigation.vue';
import HeaderRightMenu from './header-right-menu.vue';
import HeaderTabs, { MainMenu } from './header-tabs.vue';

const $router = useRouter();
const { t } = useI18n();

const mainMenu = computed<MainMenu[]>(() => [
    {
        title: t('header.dashboard'),
        icon: 'sym_o_dashboard',
        to: ROUTES.DASHBOARD.path,
        subpageNames: [],
    },
    {
        title: t('header.datasetQuality'),
        icon: 'sym_o_checklist',
        to: ROUTES.ROBOT_DATA_STUDIO.path,
        subpageNames: [
            ROUTES.ROBOT_DATA_STUDIO.name,
            ROUTES.ROBOT_DATA_STUDIO_VLM.name,
            ROUTES.ROBOT_DATA_STUDIO_IMPORT.name,
        ],
        children: [
            {
                title: t('header.datasetQuality'),
                to: ROUTES.ROBOT_DATA_STUDIO.path,
            },
            {
                title: t('header.vlmSettings'),
                to: ROUTES.ROBOT_DATA_STUDIO_VLM.path,
            },
            {
                title: t('header.importDataset'),
                to: ROUTES.ROBOT_DATA_STUDIO_IMPORT.path,
            },
            {
                title: t('header.streamMonitor'),
                to: ROUTES.STREAM_MONITOR.path,
            },
        ],
    },
    {
        title: t('header.sceneVisualization'),
        icon: 'sym_o_3d_rotation',
        to: ROUTES.SPARK_STUDIO.path,
        subpageNames: [],
    },
    {
        title: t('header.projectMgmt'),
        icon: 'sym_o_box',
        to: ROUTES.PROJECTS.path,
        subpageNames: [
            ROUTES.FILES.name,
            ROUTES.MISSIONS.name,
            ROUTES.FILE.name,
            ROUTES.PROJECT_DATASETS.name,
        ],
    },
    {
        title: t('header.dataTable'),
        icon: 'sym_o_database',
        to: ROUTES.DATATABLE.path,
        subpageNames: [],
    },
    {
        title: t('header.taskQueue'),
        icon: 'sym_o_analytics',
        to: '/actions',
        subpageNames: [ROUTES.ANALYSIS_DETAILS.name, ROUTES.ACTION.name],
    },
    {
        title: t('header.modelTraining'),
        icon: 'sym_o_model_training',
        to: ROUTES.WORLD_MODEL.path,
        subpageNames: [],
    },
    {
        title: t('header.accessControl'),
        icon: 'sym_o_lock',
        to: ROUTES.ACCESS_GROUPS.path,
        subpageNames: [ROUTES.ACCESS_GROUP.name],
    },
]);

const navigateBackToHome = async (): Promise<void> => {
    await $router.push('/');
};
</script>
