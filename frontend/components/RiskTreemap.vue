<template>
  <div ref="chartDom" class="w-full h-96 bg-gray-800 rounded-lg"></div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(["file-selected"]);

const chartDom = ref(null);
let myChart = null;

const initChart = () => {
  if (chartDom.value) {
    myChart = echarts.init(chartDom.value);
    myChart.on("click", (params) => {
      if (params.data && params.data.filename) {
        emit("file-selected", params.data.filename);
      }
    });
    setOptions();
  }
};

const setOptions = () => {
  if (!myChart) return;

  const chartData = props.data.map((file) => ({
    name: file.filename.split("/").pop(),
    value: file.risk_score,
    filename: file.filename,
  }));

  myChart.setOption({
    tooltip: {
      formatter: (info) => {
        return `<strong>${
          info.data.filename
        }</strong><br/>Risk Score: ${info.value.toFixed(2)}`;
      },
    },
    series: [
      {
        name: "Risk distribution",
        type: "treemap",
        visibleMin: 300,
        data: chartData,
        leafDepth: 1,
        levels: [
          {
            itemStyle: {
              borderColor: "#555",
              borderWidth: 1,
              gapWidth: 1,
            },
          },
        ],
        upperLabel: {
          show: true,
          height: 30,
        },
      },
    ],
    textStyle: {
      color: "#fff",
    },
  });
};

onMounted(() => {
  initChart();
});

watch(
  () => props.data,
  () => {
    setOptions();
  },
  { deep: true }
);
</script>
