<template>
  <div class="bg-gray-800 rounded-lg shadow-lg flex flex-col h-full">
    <header class="p-4 border-b border-gray-700">
      <h3 class="font-semibold text-cyan-400">AI Deep Review Report</h3>
      <p class="text-sm text-gray-400 font-mono">{{ reviewData.filename }}</p>
    </header>

    <div
      v-if="reviewData.error"
      class="m-4 p-4 bg-red-900/50 text-red-300 rounded-lg"
    >
      <p><strong>Review failed:</strong> {{ reviewData.error }}</p>
    </div>

    <div v-else class="flex flex-col">
      <!-- Code Panel-->
      <div
        ref="codePanel"
        class="bg-gray-900/50 overflow-auto max-h-[60vh] text-sm"
      >
        <div
          v-for="(line, index) in codeLines"
          :key="index"
          :class="[
            'line-wrapper',
            { 'bg-cyan-900/50': highlightedLine === index + 1 },
          ]"
          :data-line-number="index + 1"
        >
          <span class="line-number">{{ index + 1 }}</span>
          <pre
            class="line-content"
          ><code v-html="highlightSyntax(line)"></code></pre>
        </div>
      </div>

      <!-- Issues Panel -->
      <div class="p-4 space-y-4">
        <h4
          class="font-semibold text-lg text-gray-300 border-b border-gray-700 pb-2"
        >
          Detected Issues
        </h4>
        <div v-if="reviewData.review && reviewData.review.length > 0">
          <div
            v-for="(issue, index) in reviewData.review"
            :key="index"
            @click="findAndScrollToIssue(issue)"
            class="bg-gray-900 p-3 rounded-lg border border-gray-700 cursor-pointer hover:bg-gray-700/50 transition-colors duration-200"
          >
            <div class="flex items-center justify-between gap-2 mb-2">
              <span
                :class="getIssueTypeColor(issue.issue_type)"
                class="text-xs font-bold px-2.5 py-1 rounded-full"
              >
                {{ issue.issue_type }}
              </span>
            </div>
            <p class="text-sm text-gray-300">{{ issue.description }}</p>
            <div
              v-if="issue.suggestion"
              class="mt-3 pt-3 border-t border-gray-700/50"
            >
              <p class="text-xs text-cyan-300">
                <span class="font-bold text-gray-400">Suggestion:</span>
                <code class="text-xs">{{ issue.suggestion }}</code>
              </p>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-400 py-8">
          <p>🎉 AI found no issues.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import hljs from "highlight.js";
import "highlight.js/styles/tokyo-night-dark.css";

const props = defineProps({
  reviewData: {
    type: Object,
    required: true,
  },
});

const highlightedLine = ref(null);
const codePanel = ref(null);

const codeLines = computed(() => {
  if (!props.reviewData.code) return [];
  return props.reviewData.code.split(/\r\n|\n/);
});

const highlightSyntax = (line) => {
  if (line.trim() === "") return "&nbsp;";
  return hljs.highlightAuto(line).value;
};

const normalizeStringForComparison = (str) => {
  if (!str) return "";
  // Replaces all whitespace sequences (spaces, tabs, etc.) with a single space, then trims.
  return str.replace(/\s+/g, " ").trim();
};

// ---  SCROLLING LOGIC WITH TEXT MATCHING ---
const findAndScrollToIssue = async (issue) => {
  if (!codePanel.value) return;

  const normalizedSnippet = normalizeStringForComparison(issue.code_snippet);
  let targetLineNumber = -1;

  // 1. Primary method: Find line by matching the NORMALIZED code snippet
  if (normalizedSnippet) {
    // Search the entire file for the first exact normalized match
    const foundIndex = codeLines.value.findIndex((line) => {
      return normalizeStringForComparison(line) === normalizedSnippet;
    });

    if (foundIndex !== -1) {
      targetLineNumber = foundIndex + 1;
      console.log(
        `Snippet found via normalized match at actual line: ${targetLineNumber}`
      );
    } else {
      console.warn(
        `Could not find snippet via normalized match: "${normalizedSnippet}". Falling back to line number.`
      );
    }
  }

  // 2. Fallback method: Use the line number from AI if snippet matching fails
  if (targetLineNumber === -1) {
    targetLineNumber = issue.line_number;
  }

  // 3. Execute scrolling and highlighting
  highlightedLine.value = targetLineNumber;
  await nextTick();

  const lineEl = codePanel.value.querySelector(
    `[data-line-number="${targetLineNumber}"]`
  );
  if (lineEl) {
    lineEl.scrollIntoView({ behavior: "smooth", block: "center" });
  } else {
    console.error(
      `Could not find element for line number: ${targetLineNumber}`
    );
  }
};

// Reset highlight when file changes
watch(
  () => props.reviewData.filename,
  () => {
    highlightedLine.value = null;
    if (codePanel.value) codePanel.value.scrollTop = 0;
  }
);

// Smart issue type coloring
const getIssueTypeColor = (issueType) => {
  const type = String(issueType).toLowerCase();
  if (type.includes("security")) return "bg-red-800 text-red-200";
  if (type.includes("bug")) return "bg-yellow-800 text-yellow-200";
  if (type.includes("performance")) return "bg-blue-800 text-blue-200";
  if (
    type.includes("practice") ||
    type.includes("style") ||
    type.includes("quality")
  ) {
    return "bg-purple-800 text-purple-200";
  }
  return "bg-gray-700 text-gray-200";
};
</script>

<style>
.line-wrapper {
  display: flex;
  align-items: baseline; /* Align by text baseline */
}

.line-number {
  flex-shrink: 0;
  width: 4em; /* Gutter width */
  padding-right: 1em;
  text-align: right;
  color: #5f6a87;
  user-select: none; /* Make line numbers unselectable */
}

.line-content {
  flex-grow: 1;
  margin: 0;
  padding: 0;
  white-space: pre-wrap; /* Wrap long lines */
  word-break: break-all; /* Break long words/tokens */
}

/* Ensure empty lines in highlighted code are visible */
.line-content code:empty::after {
  content: " ";
}
</style>
