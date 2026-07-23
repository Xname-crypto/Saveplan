<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Clipboard,
  Download,
  Eye,
  FileText,
  History,
  Image,
  Loader2,
  Plus,
  ScanText,
  Save,
  Trash2,
  UploadCloud,
} from "lucide-vue-next"
import AppFooter from "@/components/AppFooter.vue"
import CinematicNav from "@/components/CinematicNav.vue"
import { useRouter } from "@/router"
import { authClient } from "@/services/authClient"
import {
  conversionClient,
  getConversionErrorMessage,
  isConversionAuthError,
  type CloudOcrStatus,
  type ConversionDetail,
  type ConversionAsset,
  type ConversionQuestion,
  type ConversionSummary,
  type Subject,
} from "@/services/conversionClient"

const router = useRouter()
const subjects: Array<{ id: Subject; label: string; description: string }> = [
  { id: "politics", label: "政治", description: "适合纯文本题目，保留论述语义和解析。" },
  { id: "math", label: "数学", description: "适合公式、上下标和常见数学符号。" },
  { id: "physics", label: "物理", description: "适合公式、单位和物理符号。" },
  { id: "chemistry", label: "化学", description: "适合反应式、化学式和下标内容。" },
  { id: "biology", label: "生物", description: "适合图表题和生物专有名词。" },
  { id: "general", label: "通用", description: "不确定学科时使用。" },
]

const exportFormats = [
  {
    id: "kshuati",
    label: "口袋刷题助手",
    description: "生成可复制到口袋刷题助手文本导入页的格式。",
  },
  {
    id: "shiroha",
    label: "出题试卷形式",
    description: "按普通试卷样式整理题目，适合审核、打印或导出 Word。",
  },
]

const selectedFile = ref<File | null>(null)
const selectedSubject = ref<Subject>("politics")
const selectedExportFormat = ref("kshuati")
const includeAssetProcessing = ref(false)
const pastedTitle = ref("粘贴文本")
const pastedText = ref("")
const activeConversion = ref<ConversionDetail | null>(null)
const historyItems = ref<ConversionSummary[]>([])
const exportText = ref("")
const errorMessage = ref("")
const statusMessage = ref("")
const isUploading = ref(false)
const isSaving = ref(false)
const isSavingAssets = ref(false)
const isExporting = ref(false)
const isLoadingHistory = ref(false)
const isLoadingDetail = ref(false)
const deletingHistoryId = ref<string | null>(null)
const ocrLoadingAssetId = ref<string | null>(null)
const assetPreviewUrls = ref<Record<string, string>>({})
const uploadStage = ref("")
const ocrProgressText = ref("")
const currentStep = ref(1)
const showIssueQuestions = ref(true)
const showValidQuestions = ref(true)
const issueDialogQuestion = ref<ConversionQuestion | null>(null)
const showCopySuccessDialog = ref(false)
const filePickState = ref<"idle" | "loading" | "success" | "error">("idle")
let filePickTimer: number | undefined
let uploadStageTimer: number | undefined
let copySuccessTimer: number | undefined
let ocrPollingCancelled = false
let authRedirectStarted = false

const questions = computed(() => activeConversion.value?.questions ?? [])
const assets = computed(() => activeConversion.value?.assets ?? [])
const visibleAssets = computed(() => (includeAssetProcessing.value ? assets.value : []))
const conversionIssues = computed(() => activeConversion.value?.issues ?? [])
const documentIssues = computed(() =>
  conversionIssues.value.filter((issue) => !/^第\s*\d+\s*题/.test(issue)),
)
const hasQuestions = computed(() => questions.value.length > 0)
const issueQuestions = computed(() => questions.value.filter((question) => getQuestionIssues(question).length > 0))
const validQuestions = computed(() => questions.value.filter((question) => getQuestionIssues(question).length === 0))
const issueCount = computed(() =>
  documentIssues.value.length + issueQuestions.value.reduce((total, question) => total + getQuestionIssues(question).length, 0),
)
const visibleQuestions = computed(() =>
  questions.value.filter((question) =>
    getQuestionIssues(question).length ? showIssueQuestions.value : showValidQuestions.value,
  ),
)
const uploadLabel = computed(() => selectedFile.value?.name || "选择 PDF、DOCX、DOC 或 TXT 文件")
const allowedUploadExtensions = [".pdf", ".docx", ".txt", ".doc"]
const baseOptionLabels = ["A", "B", "C", "D"]
const optionLabelPool = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("")
const subQuestionLinePattern = /^\s*[（(](\d+)[）)]\s*[.。、]?\s*(.*)$/
const assetStatusLabel = computed(() =>
  includeAssetProcessing.value ? ` · ${assets.value.length} 个待处理素材` : "",
)

function getQuestionIssues(question: ConversionQuestion | null | undefined) {
  if (!question) return []

  const issues: string[] = []
  if (!question.stem?.trim()) {
    issues.push("缺少题干")
  }

  for (const label of baseOptionLabels) {
    if (!question.options?.[label]?.trim()) {
      issues.push(`缺少${label}选项`)
    }
  }

  const answer = question.answer?.trim().toUpperCase()
  if (!answer) {
    issues.push("缺少答案")
  } else if (!getQuestionOptionLabels(question).includes(answer)) {
    issues.push("答案不在已添加选项中")
  } else if (!question.options?.[answer]?.trim()) {
    issues.push("答案对应的选项为空")
  }

  return issues
}

function getQuestionStemRows(value: string) {
  const normalized = value || ""
  const lineCount = normalized.split(/\r?\n/).reduce((total, line) => {
    return total + Math.max(1, Math.ceil(line.length / 62))
  }, 0)
  return Math.min(18, Math.max(3, lineCount))
}

function getOptionRows(value: string) {
  const normalized = value || ""
  const lineCount = normalized.split(/\r?\n/).reduce((total, line) => {
    return total + Math.max(1, Math.ceil(line.length / 72))
  }, 0)
  return Math.min(8, Math.max(1, lineCount))
}

function getQuestionOptionLabels(question: ConversionQuestion) {
  const labels = new Set(Object.keys(question.options ?? {}).map((label) => label.toUpperCase()))
  if (!labels.size) {
    baseOptionLabels.forEach((label) => labels.add(label))
  }
  return [...labels].sort((left, right) => optionLabelPool.indexOf(left) - optionLabelPool.indexOf(right))
}

function parseQuestionStemParts(question: ConversionQuestion) {
  const mainLines: string[] = []
  const subQuestions: Array<{ number: number; text: string }> = []
  for (const line of (question.stem || "").split(/\r?\n/)) {
    const match = subQuestionLinePattern.exec(line)
    if (match) {
      subQuestions.push({ number: Number(match[1]), text: match[2] || "" })
    } else {
      mainLines.push(line)
    }
  }
  return {
    mainStem: mainLines.join("\n").trimEnd(),
    subQuestions,
  }
}

function composeQuestionStem(mainStem: string, subQuestions: Array<{ number: number; text: string }>) {
  return [
    mainStem.trimEnd(),
    ...subQuestions.map((item) => `(${item.number}).${item.text ? ` ${item.text}` : ""}`),
  ].filter(Boolean).join("\n")
}

function getQuestionSubQuestions(question: ConversionQuestion) {
  return parseQuestionStemParts(question).subQuestions
}

function getQuestionPaperText(question: ConversionQuestion) {
  return `${question.number}.${parseQuestionStemParts(question).mainStem || ""}`
}

function updateQuestionPaperText(question: ConversionQuestion, value: string) {
  const mainStem = value.replace(/^\s*(?:第\s*\d+\s*题\s*[:：、.)）]?|\d+\s*[.．、)）])\s*/, "")
  question.stem = composeQuestionStem(mainStem, parseQuestionStemParts(question).subQuestions)
}

function getFileExtension(fileName: string) {
  const dotIndex = fileName.lastIndexOf(".")
  return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : ""
}

function validateSelectedFile(file: File | null) {
  if (!file) return "请先选择一个 PDF、DOCX、DOC 或 TXT 文件。"
  const extension = getFileExtension(file.name)
  if (extension === ".doc") {
    return ""
  }
  if (!allowedUploadExtensions.includes(extension)) {
    return "仅支持 PDF、DOCX、DOC 和 TXT 文件。"
  }
  return ""
}

function revokeAssetPreviewUrls() {
  Object.values(assetPreviewUrls.value).forEach((url) => URL.revokeObjectURL(url))
  assetPreviewUrls.value = {}
}

function redirectToLogin(message: string) {
  if (authRedirectStarted) return
  authRedirectStarted = true
  window.alert(message)
  authClient.logout()
  void router.push(`/login?redirect=${encodeURIComponent("/convert")}`)
}

function setError(error: unknown) {
  if (isConversionAuthError(error)) {
    redirectToLogin("登录状态已过期，请重新登录后再使用转换功能。")
    return
  }

  errorMessage.value = getConversionErrorMessage(error)
  statusMessage.value = ""
}

function waitForOcrPoll(ms: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function updateCloudOcrProgress(status: CloudOcrStatus) {
  const totalPages = status.total_pages || 0
  const extractedPages = status.extracted_pages || 0
  if (status.state === "pending") {
    uploadStage.value = "OCR 排队"
    ocrProgressText.value = "PaddleOCR 任务已提交，正在等待识别。"
  } else if (totalPages > 0) {
    uploadStage.value = `OCR 识别 ${extractedPages}/${totalPages} 页`
    ocrProgressText.value = `正在识别第 ${Math.min(extractedPages + 1, totalPages)} 页，共 ${totalPages} 页。`
  } else {
    uploadStage.value = "OCR 识别"
    ocrProgressText.value = status.message || "PaddleOCR 正在识别文档。"
  }
  statusMessage.value = status.message || ocrProgressText.value
}

async function pollCloudOcrConversion(id: string) {
  while (!ocrPollingCancelled) {
    const ocrStatus = await conversionClient.getCloudOcrStatus(id)
    updateCloudOcrProgress(ocrStatus)

    if (ocrStatus.state === "done") {
      if (!ocrStatus.conversion) {
        throw new Error("PaddleOCR 已完成，但后端没有返回转换结果。")
      }
      return ocrStatus.conversion
    }

    if (ocrStatus.state === "failed" || ocrStatus.state === "unavailable") {
      throw new Error(ocrStatus.message || "PaddleOCR 识别失败。")
    }

    await waitForOcrPoll(5000)
  }

  throw new Error("OCR 轮询已取消。")
}

async function loadHistory() {
  isLoadingHistory.value = true
  try {
    historyItems.value = await conversionClient.list()
  } catch (error) {
    setError(error)
  } finally {
    isLoadingHistory.value = false
  }
}

async function loadConversionDetail(id: string) {
  isLoadingDetail.value = true
  errorMessage.value = ""
  statusMessage.value = "正在读取转换详情..."
  exportText.value = ""

  try {
    activeConversion.value = await conversionClient.get(id)
    statusMessage.value = "已载入历史任务，可以继续校对或导出。"
  } catch (error) {
    setError(error)
  } finally {
    isLoadingDetail.value = false
  }
}

async function deleteHistoryItem(item: ConversionSummary) {
  if (!window.confirm(`确定删除“${item.filename}”这条转换历史吗？删除后无法恢复。`)) return

  deletingHistoryId.value = item.id
  errorMessage.value = ""
  statusMessage.value = "正在删除转换历史..."

  try {
    await conversionClient.delete(item.id)
    historyItems.value = historyItems.value.filter((historyItem) => historyItem.id !== item.id)
    if (activeConversion.value?.id === item.id) {
      activeConversion.value = null
      exportText.value = ""
      currentStep.value = 1
    }
    statusMessage.value = "转换历史已删除。"
  } catch (error) {
    setError(error)
  } finally {
    deletingHistoryId.value = null
  }
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  errorMessage.value = ""
  statusMessage.value = ""
  uploadStage.value = ""
  filePickState.value = "idle"
  if (filePickTimer) {
    window.clearTimeout(filePickTimer)
    filePickTimer = undefined
  }
  const validationMessage = validateSelectedFile(selectedFile.value)
  if (validationMessage) {
    errorMessage.value = validationMessage
    filePickState.value = "error"
  } else if (selectedFile.value) {
    statusMessage.value = `正在读取 ${selectedFile.value.name}...`
    filePickState.value = "loading"
    filePickTimer = window.setTimeout(() => {
      filePickState.value = "success"
      statusMessage.value = `已选择 ${selectedFile.value?.name}，下一步请选择转换配置。`
      filePickTimer = window.setTimeout(() => {
        currentStep.value = 2
      }, 1100)
    }, 800)
  }
}

async function uploadSelectedFile() {
  const file = selectedFile.value
  const validationMessage = validateSelectedFile(file)
  if (validationMessage) {
    errorMessage.value = validationMessage
    statusMessage.value = ""
    uploadStage.value = ""
    currentStep.value = 1
    return
  }

  isUploading.value = true
  ocrPollingCancelled = false
  errorMessage.value = ""
  ocrProgressText.value = ""
  uploadStage.value = "上传文件"
  statusMessage.value = "正在上传文件..."
  exportText.value = ""

  try {
    uploadStageTimer = window.setTimeout(() => {
      if (isUploading.value) {
        uploadStage.value = "后端解析"
        statusMessage.value = includeAssetProcessing.value
          ? "文件已提交，后端正在提取文本、图片和公式..."
          : "文件已提交，后端正在提取可复制文本..."
      }
    }, 900)
    if (includeAssetProcessing.value) {
      const ocrStatus = await conversionClient.startCloudOcr(file as File, selectedSubject.value)
      updateCloudOcrProgress(ocrStatus)
      activeConversion.value = await pollCloudOcrConversion(ocrStatus.id)
    } else {
      activeConversion.value = await conversionClient.upload(
        file as File,
        selectedSubject.value,
        includeAssetProcessing.value,
      )
    }
    uploadStage.value = "解析完成"
    statusMessage.value = `解析完成：识别 ${activeConversion.value.question_count} 道题，${activeConversion.value.issue_count} 个提示。`
    currentStep.value = 3
    await loadHistory()
  } catch (error) {
    setError(error)
  } finally {
    if (uploadStageTimer) {
      window.clearTimeout(uploadStageTimer)
      uploadStageTimer = undefined
    }
    isUploading.value = false
    if (errorMessage.value) uploadStage.value = "解析失败"
  }
}

async function createFromPastedText() {
  if (!pastedText.value.trim()) {
    errorMessage.value = "请先粘贴一段试卷文本或 OCR 识别结果。"
    statusMessage.value = ""
    return
  }

  isUploading.value = true
  errorMessage.value = ""
  uploadStage.value = "解析粘贴文本"
  statusMessage.value = "正在解析粘贴文本..."
  exportText.value = ""

  try {
    activeConversion.value = await conversionClient.createFromText(
      pastedTitle.value.trim() || "粘贴文本",
      pastedText.value,
      selectedSubject.value,
    )
    uploadStage.value = "解析完成"
    statusMessage.value = "粘贴文本已解析，请继续校对题目。"
    currentStep.value = 3
    await loadHistory()
  } catch (error) {
    setError(error)
  } finally {
    isUploading.value = false
    if (errorMessage.value) uploadStage.value = "解析失败"
  }
}

async function loadAssetPreviews() {
  revokeAssetPreviewUrls()
  const previewEntries: Record<string, string> = {}
  for (const asset of assets.value) {
    if (!asset.preview_url) continue
    try {
      previewEntries[asset.id] = await conversionClient.assetPreviewUrl(asset.preview_url)
    } catch (_error) {
      continue
    }
  }
  assetPreviewUrls.value = previewEntries
}

function updateOption(question: ConversionQuestion, label: string, value: string) {
  question.options = {
    ...question.options,
    [label]: value,
  }
}

function getQuestionByNumber(number: number) {
  return questions.value.find((question) => question.number === number)
}

function formatQuestionForMerge(question: ConversionQuestion) {
  const lines = [
    `${question.number}.${question.stem}`.trim(),
    ...getQuestionOptionLabels(question)
      .filter((label) => question.options[label]?.trim())
      .map((label) => `${label}. ${question.options[label].trim()}`),
  ]
  if (question.answer?.trim()) lines.push(`答案: ${question.answer.trim().toUpperCase()}`)
  if (question.analysis?.trim()) lines.push(`解析: ${question.analysis.trim()}`)
  return lines.filter(Boolean).join("\n")
}

function sortedOptionEntries(options: Record<string, string> | undefined) {
  return Object.entries(options ?? {})
    .map(([label, value]) => [label.toUpperCase(), value] as const)
    .filter(([label, value]) => optionLabelPool.includes(label) && value?.trim())
    .sort(([left], [right]) => optionLabelPool.indexOf(left) - optionLabelPool.indexOf(right))
}

function stripQuestionNumberPrefix(value: string) {
  return value.replace(/^\s*(?:第\s*\d+\s*题\s*[:：、.)）]?|\d+\s*[.．、)）])\s*/, "")
}

function createQuestionFromBlock(
  number: number,
  stem: string,
  options?: Record<string, string>,
  answer = "",
  analysis = "",
): ConversionQuestion {
  return {
    number,
    stem: stem.trimEnd(),
    options: options && Object.keys(options).length ? options : { A: "", B: "", C: "", D: "" },
    answer: answer.trim().toUpperCase(),
    analysis: analysis.trim(),
    issues: [],
  }
}

function serializeQuestionBlock(question: ConversionQuestion) {
  const lines = [`${question.number}.${stripQuestionNumberPrefix(question.stem || "")}`.trim()]
  for (const [label, value] of sortedOptionEntries(question.options)) {
    lines.push(`${label}. ${value.trim()}`)
  }
  if (question.answer?.trim()) lines.push(`答案: ${question.answer.trim().toUpperCase()}`)
  if (question.analysis?.trim()) lines.push(`解析: ${question.analysis.trim()}`)
  return lines.filter(Boolean).join("\n")
}

function parseQuestionBlocksFromText(text: string) {
  const lines = text.split(/\r?\n/)
  const blockRanges: Array<{ number: number; start: number }> = []
  const questionStartPattern = /^\s*(?:第\s*(\d+)\s*题\s*[:：、.)）]?|(\d+)\s*[.．、)）])\s*(.*)$/

  lines.forEach((line, index) => {
    const match = questionStartPattern.exec(line)
    if (match) {
      blockRanges.push({ number: Number(match[1] || match[2]), start: index })
    }
  })

  if (blockRanges.length < 2) return []

  return blockRanges.map((range, rangeIndex) => {
    const nextRange = blockRanges[rangeIndex + 1]
    const blockLines = lines.slice(range.start, nextRange?.start ?? lines.length)
    return parseQuestionBlockLines(blockLines, range.number)
  })
}

function parseQuestionBlockLines(lines: string[], fallbackNumber: number) {
  const questionStartPattern = /^\s*(?:第\s*(\d+)\s*题\s*[:：、.)）]?|(\d+)\s*[.．、)）])\s*(.*)$/
  const optionPattern = /^\s*([A-Z])\s*[.．、:：)）]\s*(.*)$/i
  const answerPattern = /^\s*(?:答案|正确答案|参考答案)\s*[:：]?\s*([A-Z])?\s*(.*)$/i
  const analysisPattern = /^\s*(?:解析|答案解析|解题思路|说明)\s*[:：]?\s*(.*)$/i

  let number = fallbackNumber
  const stemLines: string[] = []
  const options: Record<string, string> = {}
  let currentOption = ""
  let answer = ""
  const analysisLines: string[] = []
  let section: "stem" | "option" | "analysis" = "stem"

  lines.forEach((rawLine, index) => {
    const line = rawLine.trimEnd()
    const questionMatch = index === 0 ? questionStartPattern.exec(line) : null
    if (questionMatch) {
      number = Number(questionMatch[1] || questionMatch[2] || fallbackNumber)
      const firstStem = questionMatch[3] || ""
      if (firstStem.trim()) stemLines.push(firstStem)
      section = "stem"
      return
    }

    const answerMatch = answerPattern.exec(line)
    if (answerMatch) {
      answer = (answerMatch[1] || answerMatch[2] || "").trim().slice(0, 1).toUpperCase()
      section = "analysis"
      return
    }

    const analysisMatch = analysisPattern.exec(line)
    if (analysisMatch) {
      analysisLines.push(analysisMatch[1] || "")
      section = "analysis"
      return
    }

    const optionMatch = optionPattern.exec(line)
    if (optionMatch) {
      currentOption = optionMatch[1].toUpperCase()
      options[currentOption] = optionMatch[2] || ""
      section = "option"
      return
    }

    if (section === "option" && currentOption) {
      options[currentOption] = [options[currentOption], line].filter(Boolean).join("\n")
    } else if (section === "analysis") {
      analysisLines.push(line)
    } else {
      stemLines.push(line)
    }
  })

  return createQuestionFromBlock(number, stemLines.join("\n"), options, answer, analysisLines.join("\n"))
}

function renumberQuestions() {
  questions.value.forEach((question, index) => {
    question.number = index + 1
  })
}

function createEmptyQuestion(number: number): ConversionQuestion {
  return {
    number,
    stem: "",
    options: {
      A: "",
      B: "",
      C: "",
      D: "",
    },
    answer: "",
    analysis: "",
    issues: ["缺少题干", "缺少A选项", "缺少B选项", "缺少C选项", "缺少D选项", "缺少答案"],
  }
}

function addQuestion(afterNumber?: number) {
  if (!activeConversion.value) return
  activeConversion.value.questions = Array.isArray(activeConversion.value.questions)
    ? activeConversion.value.questions
    : []
  const insertIndex =
    typeof afterNumber === "number"
      ? questions.value.findIndex((question) => question.number === afterNumber) + 1
      : questions.value.length
  activeConversion.value.questions.splice(
    insertIndex > 0 ? insertIndex : questions.value.length,
    0,
    createEmptyQuestion(questions.value.length + 1),
  )
  renumberQuestions()
  exportText.value = ""
  statusMessage.value = "已新增一道单选题，请补全题干、选项和答案。"
}

function removeQuestion(index: number) {
  if (!activeConversion.value) return
  activeConversion.value.questions = Array.isArray(activeConversion.value.questions)
    ? activeConversion.value.questions
    : []
  activeConversion.value.questions.splice(index, 1)
  renumberQuestions()
  exportText.value = ""
  statusMessage.value = "题目已删除，保存或导出时会同步到后端。"
}

function removeQuestionByNumber(number: number) {
  const index = questions.value.findIndex((question) => question.number === number)
  if (index >= 0) removeQuestion(index)
}

function moveQuestionByNumber(number: number, direction: "up" | "down") {
  const index = questions.value.findIndex((question) => question.number === number)
  const targetIndex = direction === "up" ? index - 1 : index + 1
  if (index < 0 || targetIndex < 0 || targetIndex >= questions.value.length) return
  const [question] = questions.value.splice(index, 1)
  questions.value.splice(targetIndex, 0, question)
  renumberQuestions()
  exportText.value = ""
  statusMessage.value = "题目顺序已调整，保存或导出时会同步。"
}

function splitQuestionByNumber(number: number) {
  if (!activeConversion.value) return
  const index = questions.value.findIndex((question) => question.number === number)
  const question = questions.value[index]
  if (!question) return

  const blockText = serializeQuestionBlock(question)
  const parsedQuestions = parseQuestionBlocksFromText(blockText)
  if (parsedQuestions.length > 1) {
    questions.value.splice(index, 1, ...parsedQuestions)
  } else {
    questions.value.splice(index + 1, 0, createEmptyQuestion(question.number + 1))
  }
  renumberQuestions()
  exportText.value = ""
  statusMessage.value = parsedQuestions.length > 1
    ? "已按完整题块拆分，题目、选项、答案和解析会一起保留。"
    : "当前题没有识别到多道题号，已在本题后新增空题。"
  errorMessage.value = ""
}

function mergeQuestionByNumber(number: number, direction: "up" | "down") {
  if (!activeConversion.value) return
  const index = questions.value.findIndex((question) => question.number === number)
  const targetIndex = direction === "up" ? index - 1 : index
  const sourceIndex = direction === "up" ? index : index + 1
  const target = questions.value[targetIndex]
  const source = questions.value[sourceIndex]
  if (!target || !source || targetIndex === sourceIndex) return

  const mergedText = [serializeQuestionBlock(target), serializeQuestionBlock(source)].filter(Boolean).join("\n")
  target.stem = stripQuestionNumberPrefix(mergedText)
  target.options = {}
  target.answer = ""
  target.analysis = ""
  target.issues = []
  questions.value.splice(sourceIndex, 1)
  renumberQuestions()
  exportText.value = ""
  statusMessage.value = direction === "up"
    ? "已向上合并为完整题块，可再用拆分恢复。"
    : "已向下合并为完整题块，可再用拆分恢复。"
  errorMessage.value = ""
}
function addOptionByNumber(number: number) {
  const question = getQuestionByNumber(number)
  if (!question) return
  const nextLabel = optionLabelPool.find((label) => !(label in (question.options ?? {})))
  if (!nextLabel) {
    errorMessage.value = "已经没有可添加的选项标签。"
    return
  }

  question.options = {
    ...question.options,
    [nextLabel]: "",
  }
  exportText.value = ""
  statusMessage.value = `已添加 ${nextLabel} 选项。`
  errorMessage.value = ""
}

function removeOption(question: ConversionQuestion, label: string) {
  const nextOptions = { ...question.options }
  delete nextOptions[label]
  question.options = nextOptions
  if (question.answer === label) {
    question.answer = ""
  }
  exportText.value = ""
  statusMessage.value = `已删除 ${label} 选项。`
  errorMessage.value = ""
}

function updateSubQuestion(question: ConversionQuestion, subNumber: number, value: string) {
  const parts = parseQuestionStemParts(question)
  const subQuestions = parts.subQuestions.map((item) =>
    item.number === subNumber ? { ...item, text: value } : item,
  )
  question.stem = composeQuestionStem(parts.mainStem, subQuestions)
  exportText.value = ""
}

function removeSubQuestion(question: ConversionQuestion, subNumber: number) {
  const parts = parseQuestionStemParts(question)
  const subQuestions = parts.subQuestions
    .filter((item) => item.number !== subNumber)
    .map((item, index) => ({ ...item, number: index + 1 }))
  question.stem = composeQuestionStem(parts.mainStem, subQuestions)
  exportText.value = ""
  statusMessage.value = `已删除第 ${subNumber} 个子题。`
  errorMessage.value = ""
}

function addSubQuestionByNumber(number: number) {
  const question = getQuestionByNumber(number)
  if (!question) return

  const parts = parseQuestionStemParts(question)
  const existingSubNumbers = parts.subQuestions.map((item) => item.number)
  const nextSubNumber = existingSubNumbers.length ? Math.max(...existingSubNumbers) + 1 : 1
  question.stem = composeQuestionStem(parts.mainStem, [
    ...parts.subQuestions,
    { number: nextSubNumber, text: "" },
  ])
  exportText.value = ""
  statusMessage.value = `已在第 ${number} 题下添加 (${nextSubNumber}) 子题，请补全内容并选择答案。`
  errorMessage.value = ""
}

function showUnsupportedQuestionAction(action: string) {
  statusMessage.value = `${action}需要多题型结构，当前单选题 V1 暂不支持。`
  errorMessage.value = ""
}

function scrollToQuestion(number: number) {
  document.getElementById(`review-question-${number}`)?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  })
}

async function saveReview() {
  if (!activeConversion.value) return
  isSaving.value = true
  errorMessage.value = ""
  statusMessage.value = "正在保存校对结果..."

  try {
    await persistQuestions()
    exportText.value = ""
    statusMessage.value = "校对结果已保存。"
    await loadHistory()
  } catch (error) {
    setError(error)
  } finally {
    isSaving.value = false
  }
}

async function persistQuestions() {
  if (!activeConversion.value) return
  activeConversion.value = await conversionClient.saveQuestions(
    activeConversion.value.id,
    questions.value,
  )
}

function updateAssetTranscript(asset: ConversionAsset, value: string) {
  asset.transcript = value
}

function updateAssetQuestion(asset: ConversionAsset, value: string) {
  asset.target_question_number = value ? Number(value) : null
}

function updateAssetField(asset: ConversionAsset, value: string) {
  const allowedFields: ConversionAsset["target_field"][] = [
    "stem",
    "analysis",
    "option_A",
    "option_B",
    "option_C",
    "option_D",
  ]
  asset.target_field = allowedFields.includes(value as ConversionAsset["target_field"])
    ? (value as ConversionAsset["target_field"])
    : "stem"
}

function replaceAsset(updatedAsset: ConversionAsset) {
  if (!activeConversion.value) return
  activeConversion.value.assets = Array.isArray(activeConversion.value.assets)
    ? activeConversion.value.assets
    : []
  activeConversion.value.assets = activeConversion.value.assets.map((asset) =>
    asset.id === updatedAsset.id ? updatedAsset : asset,
  )
}

async function runAssetOcr(asset: ConversionAsset) {
  if (!activeConversion.value) return
  ocrLoadingAssetId.value = asset.id
  errorMessage.value = ""
  statusMessage.value = "正在尝试 OCR 识别，请稍候..."

  try {
    const result = await conversionClient.ocrAsset(activeConversion.value.id, asset.id)
    replaceAsset(result.asset)
    exportText.value = ""
    statusMessage.value = result.message
  } catch (error) {
    setError(error)
  } finally {
    ocrLoadingAssetId.value = null
  }
}

async function saveAssets() {
  if (!activeConversion.value) return
  isSavingAssets.value = true
  errorMessage.value = ""
  statusMessage.value = "正在保存图片/公式转写..."

  try {
    await persistAssets()
    exportText.value = ""
    statusMessage.value = "待处理素材已保存，生成导入文本时会自动合并已绑定内容。"
    await loadHistory()
  } catch (error) {
    setError(error)
  } finally {
    isSavingAssets.value = false
  }
}

async function persistAssets() {
  if (!activeConversion.value) return
  activeConversion.value = await conversionClient.saveAssets(activeConversion.value.id, assets.value)
}

async function exportKshuati() {
  if (!activeConversion.value) return
  isExporting.value = true
  errorMessage.value = ""
  statusMessage.value = "正在保存当前校对内容并生成导入文本..."

  try {
    await persistQuestions()
    if (includeAssetProcessing.value && assets.value.length) {
      await persistAssets()
    }
    const result = await conversionClient.exportKshuati(activeConversion.value.id)
    exportText.value = result.export_text
    statusMessage.value = `已生成 ${result.question_count} 道单选题。`
    await loadHistory()
  } catch (error) {
    setError(error)
  } finally {
    isExporting.value = false
  }
}

async function copyExportText() {
  if (!exportText.value) return
  await navigator.clipboard.writeText(exportText.value)
  statusMessage.value = "导入文本已复制。"
}

async function copyReviewedPaperText() {
  if (!activeConversion.value || !hasQuestions.value) return
  isExporting.value = true
  errorMessage.value = ""
  statusMessage.value = "正在复制试卷文本..."

  try {
    await persistQuestions()
    const paperText = questions.value.map(formatReviewedQuestionForWord).join("\n\n")
    await navigator.clipboard.writeText(paperText)
    exportText.value = ""
    statusMessage.value = ""
    showCopySuccess()
  } catch (error) {
    setError(error)
  } finally {
    isExporting.value = false
  }
}

function showCopySuccess() {
  if (copySuccessTimer) window.clearTimeout(copySuccessTimer)
  showCopySuccessDialog.value = true
  copySuccessTimer = window.setTimeout(() => {
    showCopySuccessDialog.value = false
    copySuccessTimer = undefined
  }, 1600)
}

function closeCopySuccess() {
  if (copySuccessTimer) {
    window.clearTimeout(copySuccessTimer)
    copySuccessTimer = undefined
  }
  showCopySuccessDialog.value = false
}

function downloadExportText() {
  if (!exportText.value) return
  const blob = new Blob([exportText.value], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = `${activeConversion.value?.filename || "口袋刷题"}_导入.txt`
  anchor.click()
  URL.revokeObjectURL(url)
}

function openIssueDialog(question: ConversionQuestion) {
  issueDialogQuestion.value = question
}

function closeIssueDialog() {
  issueDialogQuestion.value = null
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
}

function stripTrailingAnswerBlank(value: string) {
  return value
    .replace(/\s*(?:\(\s*\)|（\s*）)\s*$/u, "")
    .trimEnd()
}

function ensureQuestionStemBlank(value: string) {
  const trimmedValue = value.trimEnd()
  const cleanValue = stripTrailingAnswerBlank(trimmedValue)
  if (/(?:\(\s*\)|（\s*）)/u.test(cleanValue)) return cleanValue
  if (/(?:\(\s*\)|（\s*）)/u.test(trimmedValue)) return trimmedValue
  return `${cleanValue}（）`
}

function normalizeReviewedExportField(value: string) {
  return (value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .join("")
}

function shouldKeepReviewedStemLineBreak(line: string) {
  return /^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]/u.test(line)
}

function joinReviewedTextLine(left: string, right: string) {
  if (!left) return right
  if (/[\w)]$/u.test(left) && /^[\w(]/u.test(right)) return `${left} ${right}`
  return `${left}${right}`
}

function normalizeReviewedStem(value: string) {
  const lines = (value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  const normalizedLines: string[] = []

  for (const line of lines) {
    if (!normalizedLines.length || shouldKeepReviewedStemLineBreak(line)) {
      normalizedLines.push(line)
    } else {
      normalizedLines[normalizedLines.length - 1] = joinReviewedTextLine(
        normalizedLines[normalizedLines.length - 1],
        line,
      )
    }
  }

  return normalizedLines.join("\n")
}

function formatReviewedQuestionForWord(question: ConversionQuestion) {
  const stem = normalizeReviewedStem(stripQuestionNumberPrefix(question.stem || ""))
  const lines = [
    `${question.number}.${ensureQuestionStemBlank(stem)}`,
    ...sortedOptionEntries(question.options).map(([label, value]) => `${label}.${normalizeReviewedExportField(value)}`),
    `答案:${question.answer?.trim().toUpperCase() || ""}`,
    `解析:${normalizeReviewedExportField(question.analysis || "")}`,
  ]
  return lines.join("\n")
}

function escapeHtmlWithBreaks(value: string) {
  return escapeHtml(value).replace(/\r?\n/g, "<br>")
}

async function downloadReviewedWord() {
  if (!activeConversion.value) return
  await persistQuestions()
  const rows = questions.value
    .map(
      (question) => `<div class="question-block">${escapeHtmlWithBreaks(formatReviewedQuestionForWord(question))}</div>`,
    )
    .join("")
  const html = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:w="urn:schemas-microsoft-com:office:word"
      xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="utf-8">
        <title>${escapeHtml(activeConversion.value.filename)}</title>
        <style>
          body {
            font-family: "Microsoft YaHei", "SimSun", sans-serif;
            font-size: 11pt;
            line-height: 1.35;
            color: #111111;
          }
          .question-block {
            margin: 0 0 12pt 0;
            padding: 0;
            border: 0;
          }
        </style>
      </head>
      <body>
        ${rows}
      </body>
    </html>
  `
  const blob = new Blob(["\ufeff", html], { type: "application/msword;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = `${activeConversion.value.filename || "审核题目"}_人工审核.doc`
  anchor.click()
  URL.revokeObjectURL(url)
  statusMessage.value = "已生成 Word 审核文档。"
}

onMounted(() => {
  void loadHistory()
})

watch(
  () => activeConversion.value?.id,
  () => {
    void loadAssetPreviews()
  },
)

onBeforeUnmount(() => {
  ocrPollingCancelled = true
  if (uploadStageTimer) window.clearTimeout(uploadStageTimer)
  if (filePickTimer) window.clearTimeout(filePickTimer)
  if (copySuccessTimer) window.clearTimeout(copySuccessTimer)
  revokeAssetPreviewUrls()
})
</script>

<template>
  <div class="stitch-page stitch-page--workspace">
    <CinematicNav />
    <div class="stitch-noise" />
    <div class="stitch-atmosphere stitch-atmosphere--soft" />

    <main class="converter-shell converter-shell--steps">
      <header class="converter-hero stitch-reveal">
        <p class="stitch-eyebrow">KSHUATI CONVERT</p>
        <h1>试卷转换工作台</h1>
        <p>按步骤上传、配置、校对，最后输出口袋刷题导入文本或人工审核 Word 文档。</p>
      </header>

      <nav class="convert-steps" aria-label="转换步骤">
        <button :class="{ 'is-active': currentStep === 1, 'is-done': activeConversion }" @click="currentStep = 1">
          <span>1</span>
          <strong>上传文档</strong>
          <small>PDF / DOC / DOCX / TXT</small>
        </button>
        <button :class="{ 'is-active': currentStep === 2 }" @click="currentStep = 2">
          <span>2</span>
          <strong>转换配置</strong>
          <small>格式与学科</small>
        </button>
        <button :class="{ 'is-active': currentStep === 3 }" :disabled="!activeConversion" @click="currentStep = 3">
          <span>3</span>
          <strong>人工校对</strong>
          <small>修错后导出</small>
        </button>
      </nav>

      <section v-if="errorMessage || statusMessage" class="conversion-alert stitch-reveal">
        <AlertTriangle v-if="errorMessage" :size="18" />
        <CheckCircle2 v-else :size="18" />
        <span>{{ errorMessage || statusMessage }}</span>
      </section>

      <section v-show="currentStep === 1" class="step-card step-card--upload stitch-reveal">
        <div class="step-card__main">
          <label class="upload-panel upload-panel--step" aria-label="上传试卷或题库文档">
            <input
              class="sr-only"
              type="file"
              accept=".pdf,.docx,.txt,.doc,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,application/msword"
              @change="handleFileChange"
            />
            <div class="upload-panel__inner">
              <UploadCloud :size="52" />
              <h2>{{ uploadLabel }}</h2>
              <p>推荐 DOCX、PDF、TXT；旧版 DOC 会尝试自动转换，失败时请另存为 DOCX。</p>
              <span>浏览文件</span>
            </div>
            <div v-if="filePickState === 'loading' || filePickState === 'success'" class="upload-success">
              <div :class="['upload-success__mark', { 'is-loading': filePickState === 'loading' }]">
                <Loader2 v-if="filePickState === 'loading'" class="spin-icon" :size="54" />
                <CheckCircle2 v-else :size="70" />
              </div>
              <strong>{{ filePickState === "loading" ? "正在读取文件" : "文件已选择" }}</strong>
              <small>{{ filePickState === "loading" ? "正在确认文件类型与大小" : "即将进入转换配置" }}</small>
            </div>
            <div v-if="isUploading" class="upload-panel__progress">
              <i />
              <strong>{{ uploadStage || "准备上传" }}</strong>
              <span v-if="ocrProgressText">{{ ocrProgressText }}</span>
            </div>
          </label>

          <section class="paste-panel paste-panel--step" aria-label="粘贴试卷文本">
            <div>
              <p class="settings-panel__title">粘贴文本</p>
              <input v-model="pastedTitle" type="text" placeholder="任务名称，例如：政治专题一单选" />
              <textarea
                v-model="pastedText"
                rows="8"
                placeholder="把 PDF / Word / OCR 识别出的题目文本粘贴到这里，也可以粘贴末尾的答案及解析。"
              />
            </div>
            <button type="button" :disabled="isUploading || !pastedText.trim()" @click="createFromPastedText">
              <Loader2 v-if="isUploading" class="spin-icon" :size="18" />
              <FileText v-else :size="18" />
              {{ isUploading ? "解析中" : "解析粘贴文本" }}
            </button>
          </section>
        </div>

        <aside class="conversion-history conversion-history--step">
          <header>
            <History :size="18" />
            <span>转换历史</span>
          </header>
          <div v-if="isLoadingHistory" class="conversion-empty">正在读取历史...</div>
          <div v-else-if="!historyItems.length" class="conversion-empty">暂无转换记录</div>
          <article
            v-for="item in historyItems"
            v-else
            :key="item.id"
            :class="['history-item', { 'is-active': activeConversion?.id === item.id }]"
            role="button"
            tabindex="0"
            @click="loadConversionDetail(item.id); currentStep = 3"
            @keydown.enter.prevent="loadConversionDetail(item.id); currentStep = 3"
            @keydown.space.prevent="loadConversionDetail(item.id); currentStep = 3"
          >
            <div class="history-item__main">
              <strong>{{ item.filename }}</strong>
              <span>{{ item.question_count }} 题 · {{ item.subject }} · {{ item.issue_count }} 个提示</span>
            </div>
            <button
              class="history-item__delete"
              type="button"
              :disabled="deletingHistoryId === item.id"
              aria-label="删除转换历史"
              @click.stop="deleteHistoryItem(item)"
            >
              <Loader2 v-if="deletingHistoryId === item.id" class="spin-icon" :size="15" />
              <Trash2 v-else :size="15" />
            </button>
          </article>
        </aside>
      </section>

      <section v-show="currentStep === 2" class="step-card step-card--config stitch-reveal">
        <div>
          <p class="settings-panel__title">导出格式</p>
          <div class="selected-file-strip">
            <FileText :size="17" />
            <span>{{ selectedFile?.name || "尚未选择文件" }}</span>
            <button type="button" @click="currentStep = 1">重新选择</button>
          </div>
          <div class="format-options format-options--grid">
            <label
              v-for="format in exportFormats"
              :key="format.id"
              :class="['format-option', { 'is-selected': selectedExportFormat === format.id }]"
            >
              <input v-model="selectedExportFormat" type="radio" name="exportFormat" :value="format.id" />
              <CheckCircle2 v-if="selectedExportFormat === format.id" :size="18" />
              <FileText v-else :size="18" />
              <span>
                <strong>{{ format.label }}</strong>
                <small>{{ format.description }}</small>
              </span>
            </label>
          </div>
        </div>

        <div>
          <p class="settings-panel__title settings-panel__title--subject">图片 / 公式处理</p>
          <div class="asset-mode-options">
            <label :class="['format-option', { 'is-selected': !includeAssetProcessing }]">
              <input v-model="includeAssetProcessing" type="radio" name="assetMode" :value="false" />
              <FileText :size="18" />
              <span>
                <strong>仅提取文字</strong>
                <small>忽略文档图片和扫描页，校对区不显示素材处理。</small>
              </span>
            </label>
            <label :class="['format-option', { 'is-selected': includeAssetProcessing }]">
              <input v-model="includeAssetProcessing" type="radio" name="assetMode" :value="true" />
              <ScanText :size="18" />
              <span>
                <strong>PaddleOCR 图片识别 / 人工转写</strong>
                <small>扫描件和图片型试卷会先云端识别，并显示页数进度。</small>
              </span>
            </label>
          </div>
        </div>

        <div>
          <p class="settings-panel__title settings-panel__title--subject">学科规则</p>
          <div class="subject-options subject-options--step">
            <label
              v-for="subject in subjects"
              :key="subject.id"
              :class="['subject-option', { 'is-selected': selectedSubject === subject.id }]"
            >
              <input v-model="selectedSubject" type="radio" name="subject" :value="subject.id" />
              <span>
                <strong>{{ subject.label }}</strong>
                <small>{{ subject.description }}</small>
              </span>
            </label>
          </div>
        </div>

        <div v-if="isUploading" class="conversion-ocr-progress" aria-live="polite">
          <Loader2 class="spin-icon" :size="18" />
          <div>
            <strong>{{ uploadStage || "正在解析" }}</strong>
            <span>{{ ocrProgressText || statusMessage || "文件正在处理中，请稍候。" }}</span>
          </div>
        </div>

        <footer class="step-actions">
          <button type="button" @click="currentStep = 1">返回上传</button>
          <button class="primary-action" type="button" :disabled="isUploading || !selectedFile" @click="uploadSelectedFile">
            <Loader2 v-if="isUploading" class="spin-icon" :size="18" />
            <UploadCloud v-else :size="18" />
            {{ isUploading ? "解析中" : selectedFile ? "上传并解析" : "请先选择文件" }}
          </button>
          <button type="button" :disabled="!activeConversion" @click="currentStep = 3">进入校对</button>
        </footer>
      </section>

      <section v-show="currentStep === 3" class="review-workspace stitch-reveal">
        <aside class="review-sidebar">
          <header>
            <p class="stitch-eyebrow">QUESTION MAP</p>
            <strong>{{ questions.length }} 题</strong>
          </header>
          <button class="collapse-row" type="button" @click="showIssueQuestions = !showIssueQuestions">
            <ChevronDown v-if="showIssueQuestions" :size="15" />
            <ChevronRight v-else :size="15" />
            待处理 {{ issueQuestions.length }}
          </button>
          <div v-if="showIssueQuestions" class="question-map">
            <button
              v-for="question in issueQuestions"
              :key="`issue-${question.number}`"
              type="button"
              class="has-issue"
              @click="scrollToQuestion(question.number)"
            >
              {{ question.number }}
            </button>
          </div>
          <button class="collapse-row" type="button" @click="showValidQuestions = !showValidQuestions">
            <ChevronDown v-if="showValidQuestions" :size="15" />
            <ChevronRight v-else :size="15" />
            正确题 {{ validQuestions.length }}
          </button>
          <div v-if="showValidQuestions && validQuestions.length" class="question-map question-map--valid">
            <button
              v-for="question in validQuestions"
              :key="`valid-${question.number}`"
              type="button"
              @click="scrollToQuestion(question.number)"
            >
              {{ question.number }}
            </button>
          </div>
          <p v-else-if="showValidQuestions" class="question-map__empty">暂无正确题</p>
        </aside>

        <section class="review-panel review-panel--step">
          <header class="review-panel__header">
            <div class="review-panel__title">
              <p class="review-panel__label">MANUAL REVIEW</p>
              <h2>{{ isLoadingDetail ? "正在读取历史任务..." : activeConversion?.filename || "等待上传文档" }}</h2>
              <span v-if="activeConversion">
                {{ questions.length }} 道题 · {{ activeConversion.subject }} · {{ issueCount }} 个提示{{ assetStatusLabel }}
              </span>
            </div>
            <div class="review-panel__actions">
              <button type="button" :disabled="!hasQuestions || isSaving || isExporting" @click="saveReview">
                <Save :size="16" />
                保存校对
              </button>
              <button type="button" :disabled="!activeConversion || isSaving || isExporting" @click="addQuestion()">
                <Plus :size="16" />
                新增题目
              </button>
              <button type="button" :disabled="!hasQuestions" @click="downloadReviewedWord">
                <Download :size="16" />
                导出审核 Word
              </button>
              <button class="review-panel__primary-action" type="button" :disabled="!hasQuestions || isSaving || (includeAssetProcessing && isSavingAssets) || isExporting" @click="copyReviewedPaperText">
                <Clipboard :size="16" />
                {{ isExporting ? "复制中" : "复制试卷文本" }}
              </button>
            </div>
          </header>

          <div v-if="documentIssues.length" class="issue-list issue-list--document">
            <span v-for="issue in documentIssues" :key="issue">{{ issue }}</span>
          </div>

          <div v-if="visibleAssets.length" class="asset-list">
            <header class="asset-list__header">
              <div>
                <strong>待处理图片 / 扫描页 / 公式</strong>
                <span>可尝试 OCR 后人工校对，也可以直接手动转写并绑定到题干或解析。</span>
              </div>
              <button type="button" :disabled="isSavingAssets || isExporting" @click="saveAssets">
                <Save :size="15" />
                保存素材
              </button>
            </header>
            <article v-for="asset in visibleAssets" :key="asset.id">
              <img
                v-if="assetPreviewUrls[asset.id]"
                class="asset-list__preview"
                :src="assetPreviewUrls[asset.id]"
                :alt="asset.filename || '待处理图片素材'"
              />
              <div class="asset-list__meta">
                <Image :size="18" />
                <div>
                  <strong>{{ asset.kind === "scan_page" ? `PDF 第 ${asset.page || "?"} 页` : asset.filename || asset.source }}</strong>
                  <span>{{ asset.note }}</span>
                </div>
                <small>{{ asset.status === "pending_ocr" ? "等待 OCR" : "人工处理" }}</small>
              </div>
              <div class="asset-list__actions">
                <button type="button" :disabled="ocrLoadingAssetId === asset.id || !asset.stored_path" @click="runAssetOcr(asset)">
                  <Loader2 v-if="ocrLoadingAssetId === asset.id" class="spin-icon" :size="15" />
                  <ScanText v-else :size="15" />
                  {{ ocrLoadingAssetId === asset.id ? "识别中" : "尝试 OCR" }}
                </button>
              </div>
              <label>
                <small>图片/公式转写</small>
                <textarea :value="asset.transcript" rows="2" @input="updateAssetTranscript(asset, ($event.target as HTMLTextAreaElement).value)" />
              </label>
              <div class="asset-list__binding">
                <label>
                  <small>绑定题号</small>
                  <select :value="asset.target_question_number || ''" @change="updateAssetQuestion(asset, ($event.target as HTMLSelectElement).value)">
                    <option value="">不绑定</option>
                    <option v-for="question in questions" :key="question.number" :value="question.number">第 {{ question.number }} 题</option>
                  </select>
                </label>
                <label>
                  <small>插入位置</small>
                  <select :value="asset.target_field" @change="updateAssetField(asset, ($event.target as HTMLSelectElement).value)">
                    <option value="stem">题干</option>
                    <option value="analysis">解析</option>
                    <option value="option_A">A 选项</option>
                    <option value="option_B">B 选项</option>
                    <option value="option_C">C 选项</option>
                    <option value="option_D">D 选项</option>
                  </select>
                </label>
              </div>
            </article>
          </div>

          <div v-if="!activeConversion" class="conversion-empty conversion-empty--large">请先上传文档或选择历史任务。</div>
          <div v-else-if="!questions.length" class="conversion-empty conversion-empty--large">
            <span>没有识别到单选题。可以先手动新增题目，再把 OCR 或图片转写内容填进去。</span>
            <button type="button" @click="addQuestion()"><Plus :size="16" />新增单选题</button>
          </div>

          <div v-else class="question-list question-list--review">
            <article
              v-for="question in visibleQuestions"
              :key="question.number"
              :id="`review-question-${question.number}`"
              :class="['question-editor', 'question-editor--formal', { 'has-issue': getQuestionIssues(question).length }]"
            >
              <header>
                <strong>第 {{ question.number }} 题</strong>
                <div v-if="getQuestionIssues(question).length" class="question-title-issues">
                  <button
                    v-for="issue in getQuestionIssues(question)"
                    :key="`${question.number}-${issue}`"
                    type="button"
                    class="issue-button"
                    @click="openIssueDialog(question)"
                  >
                    {{ issue }}
                  </button>
                </div>
                <span v-else class="valid-badge"><CheckCircle2 :size="14" />格式完整</span>
                <button type="button" aria-label="删除题目" @click="removeQuestionByNumber(question.number)">
                  <Trash2 :size="15" />
                </button>
              </header>

              <label class="question-stem question-stem--paper">
                <textarea
                  :value="getQuestionPaperText(question)"
                  class="question-stem__textarea"
                  :rows="getQuestionStemRows(getQuestionPaperText(question))"
                  placeholder="请输入题干"
                  @input="updateQuestionPaperText(question, ($event.target as HTMLTextAreaElement).value)"
                />
              </label>

              <div v-if="getQuestionSubQuestions(question).length" class="sub-question-grid">
                <label v-for="subQuestion in getQuestionSubQuestions(question)" :key="subQuestion.number">
                  <span class="sub-question-prefix">({{ subQuestion.number }}).</span>
                  <textarea
                    :value="subQuestion.text"
                    :rows="getOptionRows(subQuestion.text)"
                    placeholder="请输入子题题目"
                    @input="updateSubQuestion(question, subQuestion.number, ($event.target as HTMLTextAreaElement).value)"
                  />
                  <button
                    class="sub-question-remove-button"
                    type="button"
                    :aria-label="`删除第${subQuestion.number}个子题`"
                    @click="removeSubQuestion(question, subQuestion.number)"
                  >
                    ×
                  </button>
                </label>
              </div>

              <div class="option-grid option-grid--formal option-grid--paper">
                <label v-for="label in getQuestionOptionLabels(question)" :key="label">
                  <span class="question-option-prefix">{{ label }}.</span>
                  <textarea
                    :value="question.options[label] || ''"
                    :rows="getOptionRows(question.options[label] || '')"
                    @input="updateOption(question, label, ($event.target as HTMLTextAreaElement).value)"
                  />
                  <button
                    class="option-remove-button"
                    type="button"
                    :aria-label="`删除${label}选项`"
                    @click="removeOption(question, label)"
                  >
                    <Trash2 :size="14" />
                  </button>
                </label>
              </div>

              <div class="answer-block answer-block--paper">
                <label class="answer-block__answer">
                  <strong>答案:</strong>
                  <input
                    :value="question.answer || ''"
                    class="answer-block__answer-input"
                    maxlength="1"
                    aria-label="正确答案"
                    placeholder="?"
                    @input="question.answer = ($event.target as HTMLInputElement).value.trim().toUpperCase()"
                  />
                  <div class="answer-block__choices" aria-label="选择正确答案">
                  <button
                      v-for="label in getQuestionOptionLabels(question)"
                      :key="label"
                      type="button"
                      :class="{ 'is-selected': question.answer === label }"
                      @click="question.answer = question.answer === label ? '' : label"
                    >
                      {{ label }}
                    </button>
                  </div>
                </label>
                <label class="answer-block__analysis">
                  <strong>解析:</strong>
                  <textarea v-model="question.analysis" rows="4" placeholder="请输入解析" />
                </label>
              </div>

              <footer class="question-paper-actions">
                <button type="button" @click="removeQuestionByNumber(question.number)">删除</button>
                <button v-if="question.number > 1" type="button" @click="moveQuestionByNumber(question.number, 'up')">上移</button>
                <button v-if="question.number < questions.length" type="button" @click="moveQuestionByNumber(question.number, 'down')">下移</button>
                <button type="button" @click="showUnsupportedQuestionAction('跨题型移')">跨题型移</button>
                <button type="button" @click="splitQuestionByNumber(question.number)">拆分</button>
                <button v-if="question.number > 1" type="button" @click="mergeQuestionByNumber(question.number, 'up')">向上合并</button>
                <button v-if="question.number < questions.length" type="button" @click="mergeQuestionByNumber(question.number, 'down')">向下合并</button>
                <button type="button" @click="addOptionByNumber(question.number)">添选项</button>
                <button type="button" @click="addSubQuestionByNumber(question.number)">添子题</button>
                <span class="question-paper-actions__score">本题 <input class="question-score-input" type="number" value="0" min="0" aria-label="本题分数" /> 分</span>
                <button class="question-paper-actions__add" type="button" aria-label="添题" @click="addQuestion(question.number)">+</button>
              </footer>
            </article>
          </div>
        </section>
      </section>

      <div v-if="showCopySuccessDialog" class="copy-success-modal" role="dialog" aria-modal="true">
        <div class="copy-success-modal__panel">
          <CheckCircle2 :size="34" />
          <strong>复制文本成功</strong>
          <button type="button" @click="closeCopySuccess">确定</button>
        </div>
      </div>

      <div v-if="issueDialogQuestion" class="issue-modal" role="dialog" aria-modal="true">
        <div class="issue-modal__panel">
          <button type="button" aria-label="关闭" @click="closeIssueDialog">×</button>
          <h3>第 {{ issueDialogQuestion?.number }} 题格式提示</h3>
          <table>
            <thead>
              <tr>
                <th>题目</th>
                <th>A</th>
                <th>B</th>
                <th>C</th>
                <th>D</th>
                <th>答案</th>
                <th>格式提示</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{{ issueDialogQuestion?.stem }}</td>
                <td>{{ issueDialogQuestion?.options.A }}</td>
                <td>{{ issueDialogQuestion?.options.B }}</td>
                <td>{{ issueDialogQuestion?.options.C }}</td>
                <td>{{ issueDialogQuestion?.options.D }}</td>
                <td>{{ issueDialogQuestion?.answer || "未填写" }}</td>
                <td>{{ getQuestionIssues(issueDialogQuestion).join("；") || "暂无格式问题" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
    <AppFooter />
  </div>
</template>

