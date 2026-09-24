<template>
    <q-tabs inline-label class="height-xxl">
        <!-- Mobile menu button -->
        <q-route-tab
            v-show="$q.screen.lt.lg"
            key="menu"
            no-caps
            class="q-py-none q-px-sm q-mx-sm text-secondary"
            label="菜单"
            icon="sym_o_menu"
        >
            <q-menu auto-close style="width: 280px">
                <q-list>
                    <template v-for="item in mainMenu" :key="item.title">
                        <!-- Items with children (dropdown) -->
                        <q-item v-if="item.children" clickable v-close-popup>
                            <q-item-section avatar>
                                <q-icon :name="item.icon" style="font-weight: bold" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ item.title }}</q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <q-icon name="sym_o_chevron_right" />
                            </q-item-section>
                            <q-menu auto-close anchor="top end" self="top start">
                                <q-list>
                                    <q-item
                                        v-for="child in item.children"
                                        :key="child.title"
                                        clickable
                                        :to="child.to"
                                    >
                                        <q-item-section>
                                            <q-item-label>{{ child.title }}</q-item-label>
                                        </q-item-section>
                                    </q-item>
                                </q-list>
                            </q-menu>
                        </q-item>
                        <!-- Regular items -->
                        <q-item v-else clickable :to="item.to">
                            <q-item-section avatar>
                                <q-icon :name="item.icon" style="font-weight: bold" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ item.title }}</q-item-label>
                            </q-item-section>
                        </q-item>
                    </template>
                </q-list>
            </q-menu>
        </q-route-tab>

        <!-- Desktop tabs -->
        <template v-for="item in mainMenu" :key="item.title">
            <!-- Items with children (dropdown) -->
            <q-btn
                v-if="item.children"
                v-show="$q.screen.gt.md"
                no-caps
                flat
                dense
                class="q-py-none q-px-sm q-mx-sm text-secondary header-dropdown-btn"
                :class="{ 'header-dropdown-active': path === item.to }"
                :label="item.title"
                :icon="item.icon"
                icon-right="sym_o_arrow_drop_down"
            >
                <q-menu auto-close anchor="bottom left" self="top left">
                    <q-list style="min-width: 180px">
                        <q-item
                            v-for="child in item.children"
                            :key="child.title"
                            clickable
                            :to="child.to"
                            :active="route.path === child.to"
                        >
                            <q-item-section>
                                <q-item-label>{{ child.title }}</q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </q-btn>
            <!-- Regular route tab -->
            <q-route-tab
                v-else
                v-show="$q.screen.gt.md"
                no-caps
                class="q-py-none q-px-sm q-mx-sm text-secondary"
                :class="{ 'q-tab--active': path === item.to }"
                :label="item.title"
                :to="item.to"
                :icon="item.icon"
            />
        </template>
    </q-tabs>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

export interface MainMenuItem {
    title: string;
    to?: string;
    icon?: string;
    subpageNames?: string[];
}

export interface MainMenu {
    title: string;
    to: string;
    icon: string;
    subpageNames: string[];
    children?: MainMenuItem[];
}

const { mainMenu } = defineProps<{ mainMenu: MainMenu[] }>();

const route = useRoute();
const path = computed(() => {
    const nameWithPostfix = `${route.name as string}Layout`;
    const menuItem = mainMenu.find((item) =>
        item.subpageNames.includes(nameWithPostfix),
    );
    return menuItem?.to ?? route.path;
});
</script>

<style scoped>
.header-dropdown-btn {
    border-radius: 0;
    min-height: 48px;
    text-transform: none;
    font-size: 14px;
    font-weight: 500;
    position: relative;
    transition: color 0.2s;
}
.header-dropdown-btn:hover {
    color: #1976d2;
}
.header-dropdown-active {
    color: #1976d2;
}
.header-dropdown-active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 4px;
    right: 4px;
    height: 2px;
    background: #1976d2;
    border-radius: 1px 1px 0 0;
}
</style>
