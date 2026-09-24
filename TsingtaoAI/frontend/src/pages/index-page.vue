<template>
    <div class="flex flex-center">
        <div class="q-pa-lg">
            <div class="text-h3 text-center">RSL Studio</div>
            <div class="text-h5 text-center">
                具身智能数据管理平台
            </div>
            <q-img src="/logo-horizontal.png" class="q-mt-md" style="max-width: 360px" />

            <!-- i18n test -->
            <div class="text-center q-mt-lg">
                <q-btn color="secondary" :label="$t('language.switchLang')" class="q-mr-sm" />
                <span class="text-h6">{{ $t('header.dashboard') }}</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts"></script>
<style scoped>
.styled-bullet-list {
    list-style-type: disc; /* Bullet style */
    margin-left: 20px; /* Indent items to allow space for bullets */
}
</style>
