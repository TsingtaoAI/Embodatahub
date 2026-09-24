<template>
    <q-card style="background-color: white" class="flex dashboard-card" flat>
        <q-card-section style="width: 100%">
            <v-chart
                :option="option"
                style="width: 100%; height: 100%"
                autoresize
            />
        </q-card-section>
    </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import VChart from 'vue-echarts';

import { BarChart, PieChart } from 'echarts/charts';
import {
    GraphicComponent,
    LegendComponent,
    TitleComponent,
    TooltipComponent,
} from 'echarts/components';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { useStorageOverview } from 'src/hooks/query-hooks';
import {
    formatSize,
} from 'src/services/general-formatting';

use([
    TitleComponent,
    PieChart,
    TooltipComponent,
    GraphicComponent,
    BarChart,
    CanvasRenderer,
    LegendComponent,
]);

const { data: storage } = useStorageOverview();

const usedBytes = computed(() => storage.value?.usedBytes ?? 0);
const totalBytes = computed(() => storage.value?.totalBytes ?? 0);
const freeBytes = computed(() => Math.max(0, totalBytes.value - usedBytes.value));
const categories = computed(() => storage.value?.categories ?? []);

const hasCategories = computed(() => categories.value.length > 0);
const hasTotalCapacity = computed(() => totalBytes.value > 0);

const option = computed(() => {
    if (hasCategories.value) {
        // ── 分类视图：按数据源显示环形图 ──
        const seriesData = categories.value.map((cat) => ({
            name: cat.name,
            value: cat.usedBytes,
            itemStyle: { color: cat.color },
        }));

        // Add free space if we know total capacity
        if (hasTotalCapacity.value && freeBytes.value > 0) {
            seriesData.push({
                name: '剩余空间',
                value: freeBytes.value,
                itemStyle: { color: '#eee' },
            });
        }

        return {
            title: {
                text: '存储空间',
                left: 'left',
                fontWeight: 'normal',
                fontSize: 16,
            },
            tooltip: {
                trigger: 'item',
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                formatter: (params: any) => {
                    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
                    const pct = params.percent != null ? ` (${params.percent}%)` : '';
                    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/restrict-template-expressions
                    return `${params.name}: ${formatSize(params.value)}${pct}`;
                },
            },
            legend: {
                show: true,
                orient: 'vertical',
                right: 0,
                top: 'middle',
                itemWidth: 12,
                itemHeight: 12,
                textStyle: {
                    fontSize: 11,
                },
            },
            series: [
                {
                    type: 'pie',
                    radius: ['55%', '75%'],
                    center: ['38%', '50%'],
                    label: {
                        show: false,
                    },
                    emphasis: {
                        label: {
                            show: true,
                            formatter: '{b}: {d}%',
                        },
                    },
                    data: seriesData,
                },
            ],
            graphic: hasTotalCapacity.value
                ? {
                      type: 'text',
                      left: '32%',
                      top: 'center',
                      style: {
                          text: `{top|${formatSize(usedBytes.value, 1000, 1)}}\n{bottom|/ ${formatSize(totalBytes.value, 1000, 1)}}`,
                          textAlign: 'center',
                          rich: {
                              top: {
                                  fontSize: 28,
                                  fill: '#000',
                              },
                              bottom: {
                                  fontSize: 14,
                                  fontWeight: 'normal',
                                  fill: '#888',
                              },
                          },
                      },
                  }
                : {
                      type: 'text',
                      left: '32%',
                      top: 'center',
                      style: {
                          text: `{top|${formatSize(usedBytes.value, 1000, 1)}}`,
                          textAlign: 'center',
                          rich: {
                              top: {
                                  fontSize: 28,
                                  fill: '#000',
                              },
                          },
                      },
                  },
        };
    }

    // ── 无分类数据时的回退视图 ──
    return {
        title: {
            text: '存储空间',
            left: 'left',
            fontWeight: 'normal',
            fontSize: 16,
        },
        tooltip: {
            trigger: 'item',
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter: (params: any) => {
                // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/restrict-template-expressions
                return `${params.name}: ${params.data?.formatted ?? params.value}`;
            },
        },
        series: [
            {
                type: 'pie',
                radius: ['75%', '80%'],
                label: {
                    show: false,
                },
                data: [
                    {
                        name: '已用',
                        value: usedBytes.value,
                        formatted: formatSize(usedBytes.value),
                        itemStyle: { color: '#0F62FE' },
                    },
                    {
                        name: '剩余',
                        value: freeBytes.value,
                        formatted: formatSize(freeBytes.value),
                        itemStyle: { color: '#eee' },
                    },
                ],
            },
        ],
        graphic: {
            type: 'text',
            left: 'center',
            top: 'center',
            style: {
                text: `{top|${formatSize(usedBytes.value, 1000, 1)}}\n{bottom|/ ${formatSize(totalBytes.value, 1000, 1)}}`,
                textAlign: 'center',
                rich: {
                    top: {
                        fontSize: 32,
                        fill: '#000',
                    },
                    bottom: {
                        fontSize: 16,
                        fontWeight: 'normal',
                        fill: '#000',
                    },
                },
            },
        },
    };
});
</script>
<style scoped></style>
