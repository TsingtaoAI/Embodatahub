<template>
    <q-page class="flex flex-center bg-grey-2">
        <q-card class="q-pa-md shadow-2 my_card" bordered>
            <q-card-section class="text-center">
                <div class="text-grey-9 text-h2 text-weight-bold">
                    403 错误
                </div>
                <div v-if="message" class="text-grey-8 text-h5">
                    {{ message }}
                </div>
                <div v-else class="text-grey-8 text-h5">
                    您没有权限访问此页面。
                </div>

                <div v-if="projectUuid" class="text-grey-8 text-h6 q-mt-lg">
                    项目 UUID：<br />
                    {{ projectUuid }}
                </div>
            </q-card-section>

            <q-card-section class="text-center q-pt-none">
                <div class="text-grey-8">
                    是否返回？
                    <a
                        href="/dashboard"
                        class="text-dark text-weight-bold"
                        style="text-decoration: none"
                    >
                        返回仪表盘。
                    </a>
                </div>
            </q-card-section>
        </q-card>
    </q-page>
</template>

<script setup lang="ts">
const urlParameters = new URLSearchParams(globalThis.location.search);
const message = urlParameters.get('message');
const projectUuid = urlParameters.get('projectUuid');
</script>
