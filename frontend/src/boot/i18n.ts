import { boot } from 'quasar/wrappers';
import { Quasar } from 'quasar';
import { createI18n } from 'vue-i18n';
import zhCNQuasar from 'quasar/lang/zh-CN';
import enUSQuasar from 'quasar/lang/en-US';
import zhCN from 'src/i18n/locales/zh-CN';
import enUS from 'src/i18n/locales/en-US';

const saved = (localStorage.getItem('rslstudio-language')) || 'zh-CN';

const i18n = createI18n({
  legacy: false,
  locale: saved,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
});

const quasarLangs: Record<string, typeof zhCNQuasar> = {
  'zh-CN': zhCNQuasar,
  'en-US': enUSQuasar,
};

// Set initial Quasar language
Quasar.lang.set(saved === 'en-US' ? enUSQuasar : zhCNQuasar);

export default boot(({ app }) => {
  app.use(i18n);
});

// Exported for use in header-right-menu etc.
export function setLocale(lang: 'zh-CN' | 'en-US') {
  i18n.global.locale.value = lang;
  localStorage.setItem('rslstudio-language', lang);
  const qLang = quasarLangs[lang];
  if (qLang) Quasar.lang.set(qLang);
}

export function getCurrentLocale(): string {
  return i18n.global.locale.value;
}
