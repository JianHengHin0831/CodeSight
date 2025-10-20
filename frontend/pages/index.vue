<template>
  <div class="bg-gray-900 min-h-screen text-white font-sans">
    <div class="container mx-auto px-4 py-12">
      <header class="text-center mb-12">
        <h1 class="text-5xl font-bold text-cyan-400">CodeSight</h1>
        <p class="text-gray-400 mt-2">
          Use AI to gain insights into the health of your GitHub repository
        </p>
      </header>

      <!-- Input Form -->
      <div class="max-w-2xl mx-auto">
        <div class="flex rounded-lg shadow-lg bg-gray-800 p-2">
          <input
            type="text"
            v-model="repoUrl"
            @keyup.enter="analyzeRepo"
            placeholder="Paste link here, for example: https://github.com/vuejs/vue"
            class="w-full bg-transparent text-gray-200 placeholder-gray-500 focus:outline-none px-4"
          />
          <button
            @click="analyzeRepo"
            :disabled="isLoading"
            class="bg-cyan-500 hover:bg-cyan-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-6 rounded-md transition duration-300"
          >
            <span v-if="!isLoading">Analyze</span>
            <span v-else>Analyzing...</span>
          </button>
        </div>
      </div>

      <div class="mt-12 max-w-7xl mx-auto">
        <!-- Error State -->
        <div
          v-if="error"
          class="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-center mt-4 max-w-3xl mx-auto"
        >
          <p class="font-bold">Analyze error</p>
          <p class="text-sm">{{ error }}</p>
        </div>

        <!-- 2. Main Analysis Section -->
        <div class="space-y-12">
          <!-- Section 2.1: Visualization -->
          <div class="space-y-4">
            <h2 class="text-2xl font-semibold text-cyan-400">
              Risk File Distribution (Treemap)
            </h2>
            <p class="text-sm text-gray-400">
              The area of each square represents its risk score. Click a square
              to view the AI review below.
            </p>
            <RiskTreemap
              v-if="analysisResult && analysisResult.bug_hotbeds.length > 0"
              :data="analysisResult.bug_hotbeds"
              @file-selected="selectFileForReview"
            />
            <div
              v-else
              class="bg-gray-800 rounded-lg h-96 flex items-center justify-center text-gray-500"
            >
              <p>No significant risk files found for analysis.</p>
            </div>
          </div>

          <!-- Section 2.2: AI Review Panel -->
          <div>
            <h2 class="text-2xl font-semibold text-cyan-400 mb-4">
              AI Review Panel
            </h2>
            <div v-if="selectedFileReview">
              <CodeReview :review-data="selectedFileReview" />
            </div>
            <div
              v-else
              class="bg-gray-800 rounded-lg min-h-[400px] flex items-center justify-center text-gray-500 text-center p-4"
            >
              <div>
                <svg
                  xmlns="http://www.w.org/2000/svg"
                  class="mx-auto h-12 w-12 text-gray-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 21h7a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v11m0 5l4.879-4.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242z"
                  />
                </svg>
                <p class="mt-4 font-semibold">Select a file to review</p>
                <p
                  v-if="analysisResult && analysisResult.ai_reviews.length > 0"
                  class="mt-1 text-sm text-gray-400"
                >
                  Click on a file in the Treemap above to view its AI review
                  report.
                </p>
                <p v-else class="mt-1 text-sm text-gray-400">
                  AI analysis is not available for the top risk files.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- Loading State -->
  <div
    v-if="isLoading"
    class="fixed inset-0 bg-black bg-opacity-90 flex flex-col justify-center items-center z-50"
  >
    <div class="rounded-2xl px-8 py-6 flex flex-col items-center shadow-lg">
      <svg
        class="animate-spin h-10 w-10 text-cyan-400 mb-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>

      <p class="text-lg text-gray-200 text-center mb-2">
        Analyzing (macro + micro) may take 30–60 seconds...
      </p>
      <p class="text-sm text-gray-400 text-center">
        AI is concurrently reviewing the top 3 high-risk files. Please be
        patient.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineComponent } from "vue";
import RiskTreemap from "~/components/RiskTreemap.vue";
import CodeReview from "~/components/CodeReview.vue";

useHead({
  title: "CodeSight – AI Code Review & Technical Debt Insights",
});

const repoUrl = ref("https://github.com/JianHengHin0831/portfolio-website");
const isLoading = ref(false);
const analysisResult = ref(null);
const error = ref(null);
const selectedFilename = ref(null);

const analyzeRepo = async () => {
  if (!repoUrl.value) {
    error.value = "Please enter a GitHub repository URL.";
    return;
  }

  isLoading.value = true;
  analysisResult.value = null;
  selectedFilename.value = null;
  error.value = null;

  try {
    const response = await $fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: repoUrl.value }),
      timeout: 120000,
    });

    analysisResult.value = response;

    // after analysis is done, automatically select the first file reviewed by AI
    if (response.ai_reviews && response.ai_reviews.length > 0) {
      // filter out reviews without errors
      const successfulReview = response.ai_reviews.find((r) => !r.error);
      if (successfulReview) {
        selectedFilename.value = successfulReview.filename;
      }
    }
  } catch (e) {
    console.error("Fetch error:", e);
    error.value =
      e.data?.detail ||
      "Analysis timed out or an unknown error occurred. Please check if the backend service is running, or try again later.";
  } finally {
    isLoading.value = false;
  }
};

const selectFileForReview = (filename) => {
  // check if this file was reviewed by AI
  if (
    analysisResult.value &&
    analysisResult.value.ai_reviews.some((r) => r.filename === filename)
  ) {
    selectedFilename.value = filename;
  } else {
    console.log("This file was not in the top 3 and was not reviewed by AI.");
    alert("This file was not in the top 3 and was not reviewed by AI.");
  }
};

const selectedFileReview = computed(() => {
  if (!selectedFilename.value || !analysisResult.value) {
    return null;
  }
  // AI only reviews top 3 file
  return analysisResult.value.ai_reviews.find(
    (r) => r.filename === selectedFilename.value
  );
});
</script>

<style>
.animate-fade-in {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
