<template>
    <q-page class="flex flex-center bg-grey-2">
        <q-card class="q-pa-md shadow-2 my_card" bordered>
            <q-card-section class="text-center">
                <div class="text-grey-9 text-h2 text-weight-bold">
                    404 错误
                </div>
                <div class="text-grey-8 text-h5">
                    您查找的页面不存在。
                </div>
            </q-card-section>

            <q-card-section class="text-center q-pt-none">
                <div class="text-grey-8">
                    是否返回？
                    <a
                        href="/"
                        class="text-dark text-weight-bold"
                        style="text-decoration: none"
                        >返回首页。</a
                    >
                </div>
            </q-card-section>
        </q-card>
    </q-page>
</template>

<script setup lang="ts"></script>
