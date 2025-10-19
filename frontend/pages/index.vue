<!-- frontend/app.vue -->
<template>
  <div class="bg-gray-900 min-h-screen text-white font-sans">
    <div class="container mx-auto px-4 py-12">
      <!-- Header -->
      <header class="text-center mb-12">
        <h1 class="text-5xl font-bold text-cyan-400">CodeSight</h1>
        <p class="text-gray-400 mt-2">用 AI 洞察 GitHub 仓库的健康状况</p>
      </header>

      <!-- Input Form -->
      <div class="max-w-2xl mx-auto">
        <div class="flex rounded-lg shadow-lg bg-gray-800 p-2">
          <input
            type="text"
            v-model="repoUrl"
            placeholder="粘贴 GitHub 仓库 URL, 例如: https://github.com/vuejs/vue"
            class="w-full bg-transparent text-gray-200 placeholder-gray-500 focus:outline-none px-4"
          />
          <button
            @click="analyzeRepo"
            :disabled="isLoading"
            class="bg-cyan-500 hover:bg-cyan-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-6 rounded-md transition duration-300"
          >
            <span v-if="!isLoading">分析</span>
            <span v-else>分析中...</span>
          </button>
        </div>
      </div>

      <!-- Results Section -->
      <div class="mt-12 max-w-4xl mx-auto">
        <!-- Loading State -->
        <div v-if="isLoading" class="text-center">
          <p class="text-lg text-gray-400">
            正在拉取数据并进行 AI 分析，请稍候...
          </p>
        </div>

        <!-- Error State -->
        <div
          v-if="error"
          class="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-lg text-center"
        >
          <p class="font-bold">分析失败</p>
          <p>{{ error }}</p>
        </div>

        <!-- Success State -->
        <div v-if="analysisResult" class="space-y-8">
          <!-- Summary Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-gray-800 p-6 rounded-lg">
              <h3 class="text-gray-400 text-sm font-medium">分析仓库</h3>
              <p class="text-2xl font-semibold text-white">
                {{ analysisResult.repo_name }}
              </p>
            </div>
            <div class="bg-gray-800 p-6 rounded-lg">
              <h3 class="text-gray-400 text-sm font-medium">技术债指数</h3>
              <p
                class="text-2xl font-semibold"
                :class="getTechDebtColor(analysisResult.tech_debt_index)"
              >
                {{ analysisResult.tech_debt_index }}
              </p>
            </div>
          </div>

          <!-- Bug Hotbeds Table -->
          <div>
            <h2 class="text-2xl font-semibold mb-4 text-cyan-400">
              Top 10 Bug 温床文件
            </h2>
            <div class="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
              <table class="w-full text-left">
                <thead class="bg-gray-700">
                  <tr>
                    <th class="p-4">风险评分</th>
                    <th class="p-4">文件路径</th>
                    <th class="p-4">修改次数</th>
                    <th class="p-4">贡献者数</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="file in analysisResult.bug_hotbeds"
                    :key="file.filename"
                    class="border-b border-gray-700 last:border-b-0 hover:bg-gray-700/50"
                  >
                    <td class="p-4 font-bold text-red-400">
                      {{ file.risk_score }}
                    </td>
                    <td class="p-4 text-gray-300 font-mono">
                      {{ file.filename }}
                    </td>
                    <td class="p-4">{{ file.modifications }}</td>
                    <td class="p-4">{{ file.authors_count }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const repoUrl = ref("");
const isLoading = ref(false);
const analysisResult = ref(null);
const error = ref(null);

const analyzeRepo = async () => {
  if (!repoUrl.value) {
    error.value = "请输入一个 GitHub 仓库 URL。";
    return;
  }

  isLoading.value = true;
  analysisResult.value = null;
  error.value = null;

  try {
    const response = await $fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: repoUrl.value }),
    });
    analysisResult.value = response;
  } catch (e) {
    error.value =
      e.data?.detail || "发生未知错误，请检查后端服务是否运行或 URL 是否正确。";
  } finally {
    isLoading.value = false;
  }
};

const getTechDebtColor = (index) => {
  if (index > 20) return "text-red-500";
  if (index > 10) return "text-yellow-500";
  return "text-green-500";
};
</script>
