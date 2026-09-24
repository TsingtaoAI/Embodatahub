<template>
    <q-tabs>
        <q-route-tab v-if="!user" :to="ROUTES.LOGIN.path">
            登录
        </q-route-tab>

        <div v-else class="flex row justify-end" style="height: 56px">
            <header-create-menu />

            <q-btn
                flat
                dense
                color="primary"
                :label="langLabel"
                style="margin: auto 4px; border: 1px solid; min-width: 50px"
            >
                <q-menu>
                    <q-list dense>
                        <q-item clickable v-close-popup @click="switchLang('zh-CN')">
                            <q-item-section>中文</q-item-section>
                        </q-item>
                        <q-item clickable v-close-popup @click="switchLang('en-US')">
                            <q-item-section>English</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </q-btn>

            <documentation-icon />

            <header-profile-menu />
        </div>
    </q-tabs>
</template>

<script setup lang="ts">
import DocumentationIcon from 'components/documentation-icon.vue';
import { useUser } from 'src/hooks/query-hooks';
import ROUTES from 'src/router/routes';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { Quasar } from 'quasar';
import zhCNQuasar from 'quasar/lang/zh-CN';
import enUSQuasar from 'quasar/lang/en-US';
import HeaderCreateMenu from './header-create-menu.vue';
import HeaderProfileMenu from './header-profile-menu.vue';

const { data: user } = useUser();

// Language switcher
const { locale } = useI18n();
const langLabel = computed(() => locale.value === 'zh-CN' ? '中文' : 'EN');
function switchLang(lang: 'zh-CN' | 'en-US') {
  locale.value = lang;
  localStorage.setItem('rslstudio-language', lang);
  Quasar.lang.set(lang === 'zh-CN' ? zhCNQuasar : enUSQuasar);
}
</script>
