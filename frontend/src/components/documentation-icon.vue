<template>
    <q-btn
        :href="documentationLink"
        round
        flat
        color="grey-8"
        target="_blank"
        icon="sym_o_help"
    >
        <q-tooltip> 帮助文档</q-tooltip>
    </q-btn>
</template>
<script setup lang="ts">
const { link } = defineProps<{ link?: string }>();

const documentationBasePath = 'https://docs.tolink.cn';
const documentationDefaultPath = '/usage/getting-started';

const documentationLink =
    link ?? documentationBasePath + documentationDefaultPath;
</script>
