<template>
  <main class="grid gap-8 px-8 py-8 lg:grid-cols-[360px_1fr]">
    <section class="space-y-6">
      <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold">Employee Classifier Tool</h2>
          <button
            class="rounded-md border border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:border-slate-500"
            @click="resetEditor"
          >
            New Rule
          </button>
        </div>

        <div v-if="loadingRules" class="mt-4 text-sm text-slate-400">Loading rules…</div>

        <div v-else class="mt-4 space-y-3">
          <label
            v-for="rule in rules"
            :key="rule.id"
            class="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/60 p-3 hover:border-slate-600"
          >
            <input v-model="selectedRuleIds" type="checkbox" :value="rule.id" class="mt-1" />
            <div class="flex-1">
              <div class="text-sm font-semibold">{{ rule.name }}</div>
              <div class="text-xs text-slate-400">
                {{ rule.type }} on <span class="font-semibold text-slate-200">{{ rule.column }}</span>
              </div>
            </div>
            <button class="text-xs text-slate-400 hover:text-slate-200" @click.prevent="editRule(rule)">
              Edit
            </button>
          </label>
        </div>
      </div>

      <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Rule Editor</h2>
        <div class="mt-4 space-y-3 text-sm">
          <div>
            <label class="text-xs text-slate-400">Name</label>
            <input v-model="editor.name" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <div v-if="editor.type !== 'conditional_required'">
              <label class="text-xs text-slate-400">Column</label>
              <input v-model="editor.column" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs text-slate-400">Type</label>
              <select v-model="editor.type" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2">
                <option value="not_empty">Not empty</option>
                <option value="number_range">Number range</option>
                <option value="allowed_values">Allowed values</option>
                <option value="conditional_required">Conditional required</option>
              </select>
            </div>
          </div>

          <div v-if="editor.type === 'number_range'" class="grid gap-3 sm:grid-cols-2">
            <div>
              <label class="text-xs text-slate-400">Min</label>
              <input v-model.number="editor.min" type="number" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs text-slate-400">Max</label>
              <input v-model.number="editor.max" type="number" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
            </div>
          </div>

          <div v-if="editor.type === 'allowed_values'">
            <label class="text-xs text-slate-400">Allowed values (comma separated)</label>
            <input v-model="allowedValuesInput" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
          </div>

          <div v-if="editor.type === 'conditional_required'" class="grid gap-3 sm:grid-cols-2">
            <div>
              <label class="text-xs text-slate-400">When column</label>
              <input v-model="editor.when_column" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs text-slate-400">Match type</label>
              <select v-model="editor.when_operator" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2">
                <option value="equals">Equals</option>
                <option value="contains">Contains</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-slate-400">Match value</label>
              <input v-model="editor.when_equals" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs text-slate-400">Then column required</label>
              <input v-model="editor.then_column" class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" />
            </div>
          </div>

          <div class="flex gap-3">
            <button class="rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-sky-400" @click="saveRule">
              Save Rule
            </button>
            <button
              class="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500"
              @click="deleteRule"
              :disabled="!editor.id"
            >
              Delete
            </button>
            <button class="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500" @click="persistRules">
              Save All
            </button>
          </div>
          <p class="text-xs text-slate-400">{{ rulesMessage }}</p>
        </div>
      </div>
    </section>

    <section class="space-y-6">
      <div
        class="rounded-xl border border-dashed border-slate-700 bg-slate-900/40 p-8 text-center"
        @dragover.prevent
        @drop.prevent="onDrop"
      >
        <div class="text-sm text-slate-300">Drag and drop an .xlsx file here</div>
        <div class="mt-2 text-xs text-slate-500">or</div>
        <label class="mt-4 inline-flex cursor-pointer items-center justify-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400">
          Choose File
          <input type="file" class="hidden" accept=".xlsx,.xls,.csv" @change="onFilePick" />
        </label>
        <div v-if="selectedFile" class="mt-4 text-xs text-slate-300">
          Selected: {{ selectedFile.name }}
        </div>
        <div class="mt-6 flex justify-center">
          <button
            class="rounded-md bg-indigo-500 px-5 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
            :disabled="!selectedFile || selectedRuleIds.length === 0 || validating"
            @click="validateFile"
          >
            {{ validating ? "Validating…" : "Validate" }}
          </button>
        </div>
      </div>

      <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Report Sheets</h2>
        <p class="mt-1 text-xs text-slate-400">Select optional report filters.</p>
        <div class="mt-4 text-sm">
          <label class="text-xs text-slate-400">Mileage Cost Multiplier</label>
          <input
            v-model.number="mileageCost"
            type="number"
            step="0.01"
            min="0"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          />
        </div>
        <div class="mt-4 border-t border-slate-800 pt-4 text-sm">
          <label class="flex items-center gap-3">
            <input v-model="disciplineFilter" type="checkbox" />
            <span>Discipline Filter</span>
          </label>
          <p class="mt-1 text-xs text-slate-400">
            Creates Terapia and Enfermeria sheets grouped by Employee from the Task column.
          </p>
        </div>
        <div class="mt-4 border-t border-slate-800 pt-4 text-sm">
          <label class="flex items-center gap-3">
            <input v-model="checkForCompletion" type="checkbox" />
            <span>Check for Completion</span>
          </label>
          <p class="mt-1 text-xs text-slate-400">
            Creates a sheet with rows where Task Status is not Completed.
          </p>
        </div>
      </div>

      <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Results</h2>
        <div v-if="validationError" class="mt-2 text-sm text-red-400">{{ validationError }}</div>
        <div v-if="validationSummary" class="mt-4 grid gap-3 sm:grid-cols-4 text-xs text-slate-300">
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Total Rows</div>
            <div class="text-lg font-semibold">{{ validationSummary.total_rows }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Failed Rows</div>
            <div class="text-lg font-semibold text-rose-400">{{ validationSummary.failed_rows }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Passed Rows</div>
            <div class="text-lg font-semibold text-emerald-400">{{ validationSummary.passed_rows }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Rules</div>
            <div class="text-lg font-semibold">{{ validationSummary.total_rules }}</div>
          </div>
        </div>
        <div v-if="validationSummary" class="mt-3 grid gap-3 sm:grid-cols-4 text-xs text-slate-300">
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Employees</div>
            <div class="text-lg font-semibold">{{ validationSummary.total_employees }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Terapia Employees</div>
            <div class="text-lg font-semibold">{{ validationSummary.terapia_employees }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Enfermeria Employees</div>
            <div class="text-lg font-semibold">{{ validationSummary.enfermeria_employees }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Unclassified Employees</div>
            <div class="text-lg font-semibold text-amber-300">{{ validationSummary.unclassified_employees }}</div>
          </div>
        </div>

        <div v-if="validationRules.length" class="mt-4 space-y-2 text-sm">
          <div
            v-for="rule in validationRules"
            :key="rule.rule_id"
            class="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/70 px-4 py-3"
          >
            <div>
              <div class="font-semibold">{{ rule.rule_name }}</div>
              <div class="text-xs text-slate-500">{{ rule.column }}</div>
            </div>
            <div class="text-right text-xs">
              <div class="text-rose-400">{{ rule.failed_rows }} failed</div>
              <div class="text-emerald-400">{{ rule.passed_rows }} passed</div>
            </div>
          </div>
        </div>

        <div class="mt-6">
          <button
            class="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500 disabled:cursor-not-allowed"
            :disabled="!reportId"
            @click="downloadReport"
          >
            Download Report (xlsx)
          </button>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

type RuleType = "not_empty" | "number_range" | "allowed_values" | "conditional_required";

interface Rule {
  id: string;
  name: string;
  type: RuleType;
  column: string;
  min?: number | null;
  max?: number | null;
  allowed?: string[] | null;
  when_column?: string | null;
  when_operator?: string | null;
  when_equals?: string | null;
  then_column?: string | null;
}

interface RuleSummary {
  rule_id: string;
  rule_name: string;
  column: string;
  failed_rows: number;
  passed_rows: number;
  total_rows: number;
}

const API_BASE = "http://127.0.0.1:8000";

const rules = ref<Rule[]>([]);
const selectedRuleIds = ref<string[]>([]);
const loadingRules = ref(true);
const rulesMessage = ref("");
const disciplineFilter = ref(false);
const checkForCompletion = ref(false);
const mileageCost = ref(1);

const editor = reactive<Rule>({
  id: "",
  name: "",
  type: "not_empty",
  column: "",
  min: null,
  max: null,
  allowed: null,
  when_column: null,
  when_operator: "equals",
  when_equals: null,
  then_column: null,
});

const allowedValuesInput = ref("");

const selectedFile = ref<File | null>(null);
const validating = ref(false);
const validationSummary = ref<any>(null);
const validationRules = ref<RuleSummary[]>([]);
const validationError = ref("");
const reportId = ref("");

const fetchRules = async () => {
  loadingRules.value = true;
  const response = await fetch(`${API_BASE}/rules`);
  const data = await response.json();
  rules.value = data;
  selectedRuleIds.value = data.map((rule: Rule) => rule.id);
  loadingRules.value = false;
};

const resetEditor = () => {
  editor.id = "";
  editor.name = "";
  editor.type = "not_empty";
  editor.column = "";
  editor.min = null;
  editor.max = null;
  editor.allowed = null;
  editor.when_column = null;
  editor.when_operator = "equals";
  editor.when_equals = null;
  editor.then_column = null;
  allowedValuesInput.value = "";
};

const editRule = (rule: Rule) => {
  editor.id = rule.id;
  editor.name = rule.name;
  editor.type = rule.type;
  editor.column = rule.column;
  editor.min = rule.min ?? null;
  editor.max = rule.max ?? null;
  editor.allowed = rule.allowed ?? null;
  editor.when_column = rule.when_column ?? null;
  editor.when_operator = rule.when_operator ?? "equals";
  editor.when_equals = rule.when_equals ?? null;
  editor.then_column = rule.then_column ?? rule.column ?? null;
  allowedValuesInput.value = (rule.allowed || []).join(", ");
};

const normalizeEditor = (): Rule => {
  const ruleId = editor.id || `rule_${crypto.randomUUID()}`;
  let allowed: string[] | null = null;
  if (editor.type === "allowed_values") {
    allowed = allowedValuesInput.value
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
  }
  return {
    id: ruleId,
    name: editor.name.trim() || "Untitled rule",
    type: editor.type,
    column: editor.type === "conditional_required" ? (editor.then_column?.trim() || "") : editor.column.trim(),
    min: editor.type === "number_range" ? editor.min ?? null : null,
    max: editor.type === "number_range" ? editor.max ?? null : null,
    allowed,
    when_column: editor.type === "conditional_required" ? (editor.when_column?.trim() || null) : null,
    when_operator: editor.type === "conditional_required" ? (editor.when_operator?.trim() || "equals") : null,
    when_equals: editor.type === "conditional_required" ? (editor.when_equals?.trim() || null) : null,
    then_column: editor.type === "conditional_required" ? (editor.then_column?.trim() || null) : null,
  };
};

const saveRule = () => {
  const rule = normalizeEditor();
  const index = rules.value.findIndex((item) => item.id === rule.id);
  if (index >= 0) {
    rules.value[index] = rule;
  } else {
    rules.value.push(rule);
    selectedRuleIds.value.push(rule.id);
  }
  rulesMessage.value = "Rule saved locally. Click Save All to persist.";
};

const deleteRule = () => {
  if (!editor.id) return;
  rules.value = rules.value.filter((rule) => rule.id !== editor.id);
  selectedRuleIds.value = selectedRuleIds.value.filter((id) => id !== editor.id);
  resetEditor();
  rulesMessage.value = "Rule removed locally. Click Save All to persist.";
};

const persistRules = async () => {
  const response = await fetch(`${API_BASE}/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rules.value),
  });
  if (!response.ok) {
    rulesMessage.value = "Failed to save rules.";
    return;
  }
  rulesMessage.value = "Rules saved to rules.json.";
  await fetchRules();
};

const onFilePick = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0];
  }
};

const onDrop = (event: DragEvent) => {
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    selectedFile.value = files[0];
  }
};

const validateFile = async () => {
  if (!selectedFile.value) return;
  validationError.value = "";
  validating.value = true;
  const payload = new FormData();
  payload.append("file", selectedFile.value);
  payload.append("rule_ids", JSON.stringify(selectedRuleIds.value));
  payload.append("discipline_filter", String(disciplineFilter.value));
  payload.append("check_for_completion", String(checkForCompletion.value));
  payload.append("mileage_cost", String(mileageCost.value));

  try {
    const response = await fetch(`${API_BASE}/validate`, { method: "POST", body: payload });
    if (!response.ok) {
      const error = await response.json();
      validationError.value = error.detail || "Validation failed.";
      validating.value = false;
      return;
    }
    const data = await response.json();
    validationSummary.value = data.summary;
    validationRules.value = data.rules;
    reportId.value = data.report_id;
  } catch (error) {
    validationError.value = "Failed to reach the validation service.";
  } finally {
    validating.value = false;
  }
};

const downloadReport = async () => {
  if (!reportId.value) return;
  const response = await fetch(`${API_BASE}/report/${reportId.value}`);
  if (!response.ok) {
    validationError.value = "Failed to download report.";
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "validation_report.xlsx";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

onMounted(async () => {
  await fetchRules();
});
</script>
