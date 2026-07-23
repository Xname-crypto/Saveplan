<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue"
import { FileText, LifeBuoy, Mail, MessageCircle, ShieldCheck, X } from "lucide-vue-next"

type LegalPanel = "privacy" | "terms" | "support" | "feedback"

interface LegalSection {
  heading: string
  paragraphs?: string[]
  items?: string[]
}

const props = withDefaults(defineProps<{
  includeFeedback?: boolean
  supportLabel?: string
}>(), {
  includeFeedback: true,
  supportLabel: "支持",
})

const activePanel = ref<LegalPanel | null>(null)

const privacySections: LegalSection[] = [
  {
    heading: "题库导入助手隐私政策",
    paragraphs: [
      "欢迎您访问我们的产品。题库导入助手（以下简称“产品和服务”）是由许先生（以下简称“我们”）开发并运营的。确保用户的数据安全和隐私保护是我们的首要任务，本隐私政策载明了您访问和使用我们的产品和服务时所收集的数据及其处理方式。本应用以商业的服务形式提供。",
      "请您在继续使用我们的产品前，务必认真仔细阅读并确认充分理解本隐私政策全部规则和要点。一旦您选择使用，即视为您同意本隐私政策的全部内容。如您不同意相关协议或其中的任何条款，应停止使用我们的产品和服务。",
      "本隐私政策帮助您了解以下内容：我们如何收集和使用您的个人信息；我们如何存储和保护您的个人信息；我们如何共享、转让、公开披露您的个人信息。",
    ],
  },
  {
    heading: "我们如何收集和使用您的个人信息",
    paragraphs: [
      "个人信息是指以电子或者其他方式记录的，能够单独或者与其他信息结合，识别特定自然人身份或者反映特定自然人活动情况的各种信息。我们根据《中华人民共和国网络安全法》和《信息安全技术个人信息安全规范》（GB/T 35273-2017）以及其它相关法律法规的要求，并严格遵循正当、合法、必要的原则，在您使用我们提供的服务或产品过程中，收集和使用您的个人信息包括但不限于邮箱等。您所提供的所有信息均来自于您本人在注册时提供的数据。",
    ],
  },
  {
    heading: "我们如何存储和保护您的个人信息",
    paragraphs: [
      "作为一般规则，我们仅在实现信息收集目的所需的时间内保留您的个人信息（例如，当您开立帐户从我们的产品获取服务时）。出于遵守法律义务或为证明某项权利或合同满足适用的诉讼时效要求的目的，我们可能需要在上述期限到期后保留您存档的个人信息，并且无法按您的要求删除。",
      "当您的个人信息对于我们的法定义务或法定时效对应的目的或档案不再必要时，我们确保将其完全删除或匿名化。如果您确认不再使用我们的产品和服务，并按照要求主动注销了您的账户，所有信息将被完全删除。",
      "我们使用符合业界标准的安全防护措施保护您提供的个人信息，并加密其中的关键数据，防止其遭到未经授权访问、公开披露、使用、修改、损坏或丢失。我们会使用加密技术确保数据的保密性；我们会使用受信赖的保护机制防止数据遭到恶意攻击。",
    ],
  },
  {
    heading: "您的权利（GDPR/CCPA）",
    paragraphs: ["根据您所在的司法管辖区，您可能有权："],
    items: [
      "访问我们持有的关于您的个人信息。",
      "请求更正或删除您的数据。",
      "反对某些类型的处理。",
    ],
  },
  {
    heading: "我们如何共享、转让、公开披露您的个人信息",
    paragraphs: [
      "在管理我们的日常业务活动所需要时，为追求合法利益以更好地服务客户，我们将合规且恰当的使用您的个人信息。出于对业务和各个方面的综合考虑，我们仅自身使用这些数据，不与任何第三方分享。",
      "我们可能会根据法律法规规定，或按政府主管部门的强制性要求，对外共享您的个人信息。在符合法律法规的前提下，当我们收到上述披露信息的请求时，我们会要求必须出具与之相应的法律文件，如传票或调查函。我们坚信，对于要求我们提供的信息，应该在法律允许的范围内尽可能保持透明。",
      "在以下情形中，共享、转让、公开披露您的个人信息无需事先征得您的授权同意：",
    ],
    items: [
      "与国家安全、国防安全直接相关的；",
      "与犯罪侦查、起诉、审判和判决执行等直接相关的；",
      "出于维护您或其他个人的生命、财产等重大合法权益但又很难得到本人同意的；",
      "您自行向社会公众公开的个人信息；",
      "从合法公开披露的信息中收集个人信息的，如合法的新闻报道、政府信息公开等渠道；",
      "根据个人信息主体要求签订和履行合同所必需的；",
      "用于维护所提供的产品或服务的安全稳定运行所必需的，例如发现、处置产品或服务的故障；",
      "法律法规规定的其他情形。",
    ],
  },
  {
    heading: "本隐私政策的变更",
    paragraphs: [
      "我们可能会不时更新我们的隐私政策。因此，建议您定期查看此页以了解更改。如有任何更改，我们会在本页公布新的隐私政策。",
      "该政策自 2026 年 7 月 23 日起生效。",
    ],
  },
  {
    heading: "联系我们",
    paragraphs: [
      "如您在阅读过程中，对本政策有任何疑问，可联系我们的客服咨询，请通过 2132984349@qq.com 或产品中的反馈方式与我们取得联系，我们将尽力在合理时间内回复并解决您的问题。",
    ],
  },
]

const termsSections: LegalSection[] = [
  {
    heading: "题库导入助手服务条款",
    paragraphs: [
      "欢迎使用题库导入助手。您访问或使用本产品，即表示您已阅读、理解并同意遵守本服务条款。如您不同意本条款，请停止使用本产品和服务。",
      "本服务条款自 2026 年 7 月 23 日起生效。",
    ],
  },
  {
    heading: "服务内容",
    paragraphs: [
      "题库导入助手提供资料上传、文本解析、OCR/AI 识别、题目校对、格式整理与导出等学习辅助功能。我们会持续改进服务，但不保证所有文件、图片或题型在任何情况下都能被完整、准确识别。",
    ],
  },
  {
    heading: "账号与安全",
    paragraphs: [
      "您需要提供真实、有效的注册信息，并妥善保管账号、密码和登录状态。因您主动泄露、共用账号或保管不当导致的损失，由您自行承担。",
    ],
  },
  {
    heading: "用户内容",
    paragraphs: [
      "您上传的试卷、图片、文本、题目和其他资料应当由您合法拥有或已获得授权。您不得上传侵犯他人知识产权、隐私权、名誉权或违反法律法规的内容。",
      "我们仅为提供转换、校对、导出等服务目的处理您上传的内容，不会主动将您的资料分享给第三方。",
    ],
  },
  {
    heading: "付费与服务变更",
    paragraphs: [
      "部分功能可能以商业服务形式提供。具体价格、权益、次数限制和服务期限以页面展示为准。我们可能根据产品运营情况调整功能、价格或套餐内容，并会在合理范围内进行提示。",
    ],
  },
  {
    heading: "免责声明",
    paragraphs: [
      "本产品生成或整理的题目、答案、解析和导出结果仅供学习参考，不构成考试、教学或学术结论。您应自行校对和判断内容准确性。",
      "因网络、浏览器、第三方云服务、不可抗力或用户操作不当导致服务中断、数据异常或使用受限的，我们将在合理范围内协助处理，但不承担超出法律规定范围的责任。",
    ],
  },
  {
    heading: "联系我们",
    paragraphs: ["如您对本服务条款有疑问，请通过 2132984349@qq.com 与我们联系。"],
  },
]

const supportSections: LegalSection[] = [
  {
    heading: "帮助支持",
    paragraphs: [
      "如果您在注册登录、资料上传、OCR 识别、题目校对、导出格式或账号使用中遇到问题，可以通过以下方式联系我们。",
    ],
    items: [
      "客服邮箱：2132984349@qq.com",
      "请尽量附上问题页面、操作步骤、浏览器提示和截图，方便我们更快定位问题。",
      "我们会尽力在合理时间内回复并协助解决。",
    ],
  },
]

const feedbackSections: LegalSection[] = [
  {
    heading: "问题反馈",
    paragraphs: [
      "如果您希望反馈问题、提出功能建议、报告页面异常或咨询账号与套餐相关事项，可以通过客服邮箱联系我们。",
    ],
    items: [
      "反馈邮箱：2132984349@qq.com",
      "建议写清楚您正在使用的页面、点击了哪个按钮、遇到的提示或报错。",
      "如果方便，请附上截图、浏览器控制台报错或复现步骤，我们会更快定位问题。",
    ],
  },
]

const panelMeta = computed(() => {
  if (activePanel.value === "privacy") {
    return {
      title: "隐私政策",
      eyebrow: "PRIVACY POLICY",
      icon: ShieldCheck,
      sections: privacySections,
    }
  }

  if (activePanel.value === "terms") {
    return {
      title: "服务条款",
      eyebrow: "TERMS OF SERVICE",
      icon: FileText,
      sections: termsSections,
    }
  }

  if (activePanel.value === "feedback") {
    return {
      title: "问题反馈",
      eyebrow: "FEEDBACK",
      icon: MessageCircle,
      sections: feedbackSections,
    }
  }

  return {
    title: "帮助支持",
    eyebrow: "SUPPORT",
    icon: LifeBuoy,
    sections: supportSections,
  }
})

function openPanel(panel: LegalPanel) {
  activePanel.value = panel
  document.body.style.overflow = "hidden"
}

function closePanel() {
  activePanel.value = null
  document.body.style.overflow = ""
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape" && activePanel.value) {
    closePanel()
  }
}

window.addEventListener("keydown", handleKeydown)

onBeforeUnmount(() => {
  document.body.style.overflow = ""
  window.removeEventListener("keydown", handleKeydown)
})
</script>

<template>
  <nav class="legal-links" aria-label="法律与支持链接">
    <button class="legal-link" type="button" @click="openPanel('privacy')">隐私政策</button>
    <button class="legal-link" type="button" @click="openPanel('terms')">服务条款</button>
    <button class="legal-link" type="button" @click="openPanel('support')">{{ props.supportLabel }}</button>
    <button v-if="props.includeFeedback" class="legal-link" type="button" @click="openPanel('feedback')">反馈</button>
  </nav>

  <Teleport to="body">
    <div v-if="activePanel" class="legal-modal" role="dialog" aria-modal="true" :aria-label="panelMeta.title">
      <button class="legal-modal__backdrop" type="button" aria-label="关闭弹窗" @click="closePanel"></button>
      <section class="legal-modal__panel">
        <header class="legal-modal__header">
          <div>
            <span class="legal-modal__eyebrow">{{ panelMeta.eyebrow }}</span>
            <h2>{{ panelMeta.title }}</h2>
          </div>
          <component :is="panelMeta.icon" :size="24" />
          <button class="legal-modal__close" type="button" aria-label="关闭" @click="closePanel">
            <X :size="20" />
          </button>
        </header>

        <div class="legal-modal__body">
          <article v-for="section in panelMeta.sections" :key="section.heading" class="legal-modal__section">
            <h3>{{ section.heading }}</h3>
            <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
            <ul v-if="section.items?.length">
              <li v-for="item in section.items" :key="item">{{ item }}</li>
            </ul>
          </article>
        </div>

        <footer class="legal-modal__footer">
          <a href="mailto:2132984349@qq.com">
            <Mail :size="16" />
            2132984349@qq.com
          </a>
          <button type="button" @click="closePanel">我已了解</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.legal-links {
  display: flex;
  align-items: center;
}

.legal-link {
  border: 0;
  padding: 0;
  background: transparent;
  color: rgba(235, 228, 207, 0.84);
  cursor: pointer;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;
  transition: color 180ms ease, text-shadow 180ms ease;
}

.legal-link:hover,
.legal-link:focus-visible {
  color: #f3ead0;
  outline: none;
  text-shadow: 0 0 14px rgba(214, 197, 141, 0.24);
}

.legal-modal {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: grid;
  place-items: center;
  padding: clamp(1rem, 3vw, 2rem);
}

.legal-modal__backdrop {
  position: absolute;
  inset: 0;
  border: 0;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.legal-modal__panel {
  position: relative;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  width: min(48rem, calc(100vw - 2rem));
  max-height: min(82vh, 46rem);
  overflow: hidden;
  border: 1px solid rgba(235, 228, 207, 0.18);
  border-radius: 1.15rem;
  background:
    linear-gradient(180deg, rgba(235, 228, 207, 0.08), transparent 38%),
    #11100e;
  color: rgba(235, 228, 207, 0.78);
  box-shadow:
    0 36px 120px rgba(0, 0, 0, 0.58),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.legal-modal__header {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 1rem;
  padding: clamp(1.25rem, 3vw, 1.8rem);
  border-bottom: 1px solid rgba(235, 228, 207, 0.1);
}

.legal-modal__header h2 {
  margin: 0.35rem 0 0;
  color: #f1ead5;
  font-family: var(--font-display);
  font-size: clamp(1.85rem, 4vw, 2.7rem);
  font-weight: 500;
  letter-spacing: 0;
  line-height: 1;
}

.legal-modal__eyebrow {
  color: rgba(214, 197, 141, 0.82);
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.2em;
}

.legal-modal__close {
  display: inline-grid;
  width: 2.45rem;
  height: 2.45rem;
  place-items: center;
  border: 1px solid rgba(235, 228, 207, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.035);
  color: #ebe4cf;
  cursor: pointer;
}

.legal-modal__body {
  overflow: auto;
  padding: clamp(1.15rem, 3vw, 1.8rem);
}

.legal-modal__section + .legal-modal__section {
  margin-top: 1.35rem;
}

.legal-modal__section h3 {
  margin: 0 0 0.65rem;
  color: #f1ead5;
  font-size: 1rem;
  font-weight: 900;
  line-height: 1.4;
}

.legal-modal__section p,
.legal-modal__section li {
  color: rgba(235, 228, 207, 0.72);
  font-size: 0.92rem;
  line-height: 1.85;
}

.legal-modal__section p {
  margin: 0.65rem 0 0;
}

.legal-modal__section ul {
  display: grid;
  gap: 0.45rem;
  margin: 0.75rem 0 0;
  padding-left: 1.25rem;
}

.legal-modal__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem clamp(1.25rem, 3vw, 1.8rem);
  border-top: 1px solid rgba(235, 228, 207, 0.1);
}

.legal-modal__footer a {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: rgba(235, 228, 207, 0.72);
  font-size: 0.82rem;
  font-weight: 800;
  text-decoration: none;
}

.legal-modal__footer button {
  min-height: 2.5rem;
  border: 1px solid rgba(235, 228, 207, 0.78);
  border-radius: 999px;
  padding: 0 1.35rem;
  background: #ebe4cf;
  color: #111;
  cursor: pointer;
  font-weight: 900;
}

@media (max-width: 640px) {
  .legal-links {
    flex-wrap: wrap;
    justify-content: center;
  }

  .legal-modal {
    padding: 0.7rem;
  }

  .legal-modal__panel {
    width: 100%;
    max-height: calc(100svh - 1.4rem);
    border-radius: 0.95rem;
  }

  .legal-modal__header {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .legal-modal__header > svg {
    display: none;
  }

  .legal-modal__footer {
    align-items: stretch;
    flex-direction: column;
  }

  .legal-modal__footer button {
    width: 100%;
  }
}
</style>
