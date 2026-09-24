<template>
    <div class="flex flex-center bg-grey-2" style="height: calc(100vh - 50px)">
        <div
            style="
                border-radius: 0;
                display: grid;
                grid-template-columns: 48px 460px 48px;
                grid-template-rows: 48px auto 48px;
            "
        >
            <div
                style="
                    border-bottom: 1px solid #e0e0e0;
                    border-right: 1px solid #e0e0e0;
                "
            />
            <div style="border-bottom: 1px solid #e0e0e0" />
            <div
                style="
                    border-bottom: 1px solid #e0e0e0;
                    border-left: 1px solid #e0e0e0;
                "
            />

            <div style="border-right: 1px solid #e0e0e0" />
            <div
                style="
                    background: white;
                    display: flex;
                    padding: 48px;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                "
            >
                <div style="width: 100%">
                    <img
                        src="/logo-vertical.png"
                        style="height: 64px; margin-bottom: 24px"
                    />

                    <h1
                        style="
                            font-size: 28px;
                            font-weight: 400;
                            margin-bottom: 24px;
                            margin-top: 0;
                            line-height: 36px;
                        "
                    >
                        登录 RSL Studio
                    </h1>

                    <!-- Loading state -->
                    <div
                        v-if="isLoadingProviders"
                        class="q-mb-md"
                        style="display: flex; justify-content: center"
                    >
                        <q-spinner color="primary" size="48px" />
                    </div>

                    <!-- Backend unavailable warning -->
                    <div
                        v-else-if="isProvidersError || noProvidersAvailable"
                        class="q-mb-md q-pa-md"
                        style="
                            background-color: #fff3cd;
                            border: 1px solid #ffc107;
                            border-radius: 4px;
                            color: #856404;
                        "
                    >
                        <div style="font-weight: 500; margin-bottom: 8px">
                            后端不可用
                        </div>
                        <div style="font-size: 14px">
                            认证后端暂时不可用，请稍后重试或联系系统管理员。
                        </div>
                        <q-btn
                            label="重新连接"
                            color="warning"
                            flat
                            class="q-mt-sm full-width"
                            @click="handleRefetchProviders"
                        />
                    </div>

                    <!-- Normal login/register UI -->
                    <template v-else>
                        <!-- Tab toggle: Login / Register -->
                        <div class="q-mb-lg">
                            <q-btn
                                flat
                                :color="mode === 'login' ? 'primary' : 'grey-7'"
                                :class="{ 'text-weight-bold': mode === 'login' }"
                                label="登录"
                                @click="mode = 'login'"
                                no-caps
                            />
                            <q-btn
                                flat
                                :color="mode === 'register' ? 'primary' : 'grey-7'"
                                :class="{ 'text-weight-bold': mode === 'register' }"
                                label="注册"
                                @click="mode = 'register'"
                                no-caps
                            />
                        </div>

                        <!-- Email / Password Form -->
                        <q-form @submit="onSubmit" class="q-gutter-md">
                            <!-- Registration-only: Name -->
                            <q-input
                                v-if="mode === 'register'"
                                v-model="name"
                                label="姓名"
                                :rules="[
                                    (val: string) => !!val || '请输入姓名',
                                ]"
                                outlined
                                dense
                                :disable="isSubmitting"
                            />

                            <!-- Email -->
                            <q-input
                                v-model="email"
                                label="邮箱"
                                type="email"
                                :rules="[
                                    (val: string) => !!val || '请输入邮箱',
                                    (val: string) => /.+@.+/.test(val) || '邮箱格式不正确',
                                ]"
                                outlined
                                dense
                                :disable="isSubmitting"
                            />

                            <!-- Password -->
                            <q-input
                                v-model="password"
                                label="密码"
                                type="password"
                                :rules="[
                                    (val: string) => !!val || '请输入密码',
                                    (val: string) => val.length >= 8 || '密码至少 8 个字符',
                                ]"
                                outlined
                                dense
                                :disable="isSubmitting"
                            />

                            <!-- Registration-only: Confirm Password -->
                            <q-input
                                v-if="mode === 'register'"
                                v-model="confirmPassword"
                                label="确认密码"
                                type="password"
                                :rules="[
                                    (val: string) => !!val || '请确认密码',
                                    (val: string) => val === password || '两次密码不一致',
                                ]"
                                outlined
                                dense
                                :disable="isSubmitting"
                            />

                            <!-- Submit button -->
                            <q-btn
                                type="submit"
                                :label="mode === 'login' ? '登录' : '注册'"
                                color="primary"
                                class="full-width"
                                :loading="isSubmitting"
                                no-caps
                            />
                        </q-form>

                        <!-- Divider -->
                        <div
                            class="q-mt-lg q-mb-md text-grey-6"
                            style="font-size: 14px; display: flex; align-items: center"
                        >
                            <q-separator style="flex: 1" />
                            <span class="q-mx-sm">或使用第三方登录</span>
                            <q-separator style="flex: 1" />
                        </div>

                        <!-- OAuth buttons -->
                        <template v-if="availableProviders">
                            <q-btn
                                v-if="availableProviders.fakeOauth"
                                class="button-border full-width"
                                flat
                                outline
                                size="md"
                                label="开发者登录（模拟 OAuth）"
                                @click="loginWithFakeOAuth"
                            />
                           <q-btn
                                v-if="availableProviders.google"
                                class="button-border full-width q-mt-md"
                                flat
                                outline
                                size="md"
                                label="使用 Google 登录"
                                @click="loginWithGoogle"
                            />
                            <q-btn
                                v-if="availableProviders.github"
                                class="button-border full-width q-mt-md"
                                flat
                                outline
                                size="md"
                                label="使用 GitHub 登录"
                                @click="loginWithGitHub"
                            />
                        </template>
                    </template>

                    <div v-if="$route.query.error_msg" class="q-mt-lg">
                        <span class="text-negative">
                            {{ $route.query.error_msg }}
                        </span>
                    </div>
                </div>
            </div>
            <div style="border-left: 1px solid #e0e0e0" />

            <div
                style="
                    border-top: 1px solid #e0e0e0;
                    border-right: 1px solid #e0e0e0;
                "
            />
            <div style="border-top: 1px solid #e0e0e0" />
            <div
                style="
                    border-top: 1px solid #e0e0e0;
                    border-left: 1px solid #e0e0e0;
                "
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import { useMutation, useQuery } from '@tanstack/vue-query';
import {
    getAvailableProviders,
    login,
    loginWithEmail,
    registerWithEmail,
} from 'src/services/auth';
import { getMe } from 'src/services/queries/user';
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';

const $router = useRouter();
const $q = useQuasar();

const mode = ref<'login' | 'register'>('login');
const email = ref('');
const name = ref('');
const password = ref('');
const confirmPassword = ref('');
const isSubmitting = ref(false);

const {
    data: availableProviders,
    isLoading: isLoadingProviders,
    isError: isProvidersError,
    refetch: refetchProviders,
} = useQuery({
    queryKey: ['available-providers'],
    queryFn: getAvailableProviders,
    staleTime: Infinity,
    retry: false,
    refetchInterval: (query) => (query.state.error ? 5000 : false),
});

const { data: me, error } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    staleTime: 100,
    refetchInterval: 5000,
});

const noProvidersAvailable = computed(() => {
    if (!availableProviders.value) return false;
    return (
        !availableProviders.value.google &&
        !availableProviders.value.github &&
        !availableProviders.value.fakeOauth
    );
});

const loginWithGoogle = (): void => {
    login('google');
};
const loginWithGitHub = (): void => {
    login('github');
};
const loginWithFakeOAuth = (): void => {
    login('fake-oauth');
};

const onSubmit = async () => {
    isSubmitting.value = true;
    try {
        if (mode.value === 'login') {
            await loginWithEmail(email.value, password.value);
        } else {
            await registerWithEmail(name.value, email.value, password.value);
        }
        $q.notify({
            message: mode.value === 'login' ? '登录成功' : '注册成功',
            color: 'positive',
            position: 'top',
        });
        // Reload to clear auth cache and trigger route guard redirect
        globalThis.location.reload();
    } catch (err: unknown) {
        const axiosError = err as {
            response?: { data?: { message?: string } };
        };
        const message =
            axiosError?.response?.data?.message || '操作失败，请重试';
        $q.notify({
            message,
            color: 'negative',
            position: 'top',
        });
    } finally {
        isSubmitting.value = false;
    }
};

watch(
    [me, error],
    async ([_me, _error]) => {
        if (!!_me?.uuid && !_error) {
            await $router.push('/');
        }
    },
    { immediate: true },
);

const handleRefetchProviders = () => {
    void refetchProviders();
};
</script>
