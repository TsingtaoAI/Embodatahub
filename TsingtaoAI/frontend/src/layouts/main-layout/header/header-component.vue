<template>
    <q-header class="bg-default text-grey-8 q-px-lg">
        <q-toolbar class="q-pa-none height-xxl">
            <q-toolbar-title
                shrink
                class="q-pa-none"
                @click="navigateBackToHome"
            >
                <kleinkram-logo class="q-pr-lg" />
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
import KleinkramLogo from 'src/components/images/kleinkram-logo.vue';
import ROUTES from 'src/router/routes';
import { useRouter } from 'vue-router';
import BreadCrumbsNavigation from './bread-crumb-navigation.vue';
import HeaderRightMenu from './header-right-menu.vue';
import HeaderTabs, { MainMenu } from './header-tabs.vue';

const $router = useRouter();

const mainMenu: MainMenu[] = [
    {
        title: '仪表盘',
        icon: 'sym_o_dashboard',
        to: ROUTES.DASHBOARD.path,
        subpageNames: [],
    },
    {
        title: '项目管理',
        icon: 'sym_o_box',
        to: ROUTES.PROJECTS.path,
        subpageNames: [
            ROUTES.FILES.name,
            ROUTES.MISSIONS.name,
            ROUTES.FILE.name,
        ],
    },
    {
        title: '数据表',
        icon: 'sym_o_database',
        to: ROUTES.DATATABLE.path,
        subpageNames: [],
    },
    {
        title: '任务队列',
        icon: 'sym_o_analytics',
        to: '/actions',
        subpageNames: [ROUTES.ANALYSIS_DETAILS.name, ROUTES.ACTION.name],
    },
    {
        title: '权限控制',
        icon: 'sym_o_lock',
        to: ROUTES.ACCESS_GROUPS.path,
        subpageNames: [ROUTES.ACCESS_GROUP.name],
    },
];

const navigateBackToHome = async (): Promise<void> => {
    await $router.push('/');
};
</script>
