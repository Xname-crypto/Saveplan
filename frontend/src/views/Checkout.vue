<script setup lang="ts">
import { computed, nextTick, ref } from "vue"
import {
  ArrowLeft,
  Check,
  CircleAlert,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Phone,
  ShieldCheck,
  UserRound,
} from "lucide-vue-next"
import AppFooter from "@/components/AppFooter.vue"
import CinematicNav from "@/components/CinematicNav.vue"
import { useRoute, useRouter } from "@/router"
import { getStoredAuthUser } from "@/services/authClient"
import { getOrderErrorMessage, orderClient } from "@/services/orderClient"
import { getPlanById } from "@/services/planCatalog"

interface CheckoutForm {
  contactName: string
  contactPhone: string
  contactEmail: string
  agreed: boolean
}

type FormField = keyof CheckoutForm

const router = useRouter()
const route = useRoute()
const storedUser = getStoredAuthUser()
const selectedPlan = computed(() => getPlanById(route.query.plan))
const form = ref<CheckoutForm>({
  contactName: storedUser?.username ?? "",
  contactPhone: "",
  contactEmail: storedUser?.email ?? "",
  agreed: false,
})
const fieldErrors = ref<Partial<Record<FormField, string>>>({})
const requestError = ref("")
const isSubmitting = ref(false)

function returnToPricing() {
  void router.push("/pricing")
}

function validateForm() {
  const nextErrors: Partial<Record<FormField, string>> = {}

  if (form.value.contactName.trim().length < 2) {
    nextErrors.contactName = "请填写至少 2 个字的姓名。"
  }

  if (!/^1\d{10}$/.test(form.value.contactPhone.trim())) {
    nextErrors.contactPhone = "请输入有效的 11 位手机号。"
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.contactEmail.trim())) {
    nextErrors.contactEmail = "请输入有效的邮箱地址。"
  }

  if (!form.value.agreed) {
    nextErrors.agreed = "请先阅读并同意服务条款。"
  }

  fieldErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

async function focusFirstInvalidField() {
  await nextTick()
  const field = Object.keys(fieldErrors.value)[0] as FormField | undefined
  if (!field) return

  document.querySelector<HTMLElement>(`[name="${field}"]`)?.focus()
}

async function confirmOrder() {
  requestError.value = ""

  if (!selectedPlan.value) {
    returnToPricing()
    return
  }

  if (!validateForm()) {
    await focusFirstInvalidField()
    return
  }

  isSubmitting.value = true

  try {
    const order = await orderClient.createPendingOrder({
      plan_id: selectedPlan.value.id,
      contact_name: form.value.contactName.trim(),
      contact_phone: form.value.contactPhone.trim(),
      contact_email: form.value.contactEmail.trim(),
    })

    window.location.assign(order.payment_url)
  } catch (error) {
    requestError.value = getOrderErrorMessage(error)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="stitch-page checkout-page">
    <CinematicNav />
    <div class="stitch-noise" />

    <main class="checkout-shell">
      <button type="button" class="checkout-back" @click="returnToPricing">
        <ArrowLeft :size="18" />
        返回选择套餐
      </button>

      <section v-if="selectedPlan" class="checkout-grid">
        <div class="checkout-form-column">
          <header class="checkout-heading">
            <p class="stitch-eyebrow">ORDER CONFIRMATION</p>
            <h1>确认你的订单</h1>
            <p>填写联系信息后，我们将创建待支付订单并跳转至 Z-Pay 收银台。</p>
          </header>

          <form class="checkout-form" novalidate @submit.prevent="confirmOrder">
            <div v-if="requestError" class="checkout-alert" role="alert">
              <CircleAlert :size="19" />
              <span>{{ requestError }}</span>
            </div>

            <section class="checkout-form-section" aria-labelledby="contact-details">
              <div class="checkout-section-heading">
                <span>01</span>
                <div>
                  <h2 id="contact-details">联系信息</h2>
                  <p>用于发送订单与支付状态提醒。</p>
                </div>
              </div>

              <label class="checkout-field">
                <span>姓名</span>
                <div :class="{ 'has-error': fieldErrors.contactName }">
                  <UserRound :size="18" />
                  <input
                    v-model="form.contactName"
                    name="contactName"
                    type="text"
                    autocomplete="name"
                    placeholder="请输入你的姓名"
                    :aria-invalid="Boolean(fieldErrors.contactName)"
                    @input="fieldErrors.contactName = undefined"
                  />
                </div>
                <small v-if="fieldErrors.contactName">{{ fieldErrors.contactName }}</small>
              </label>

              <label class="checkout-field">
                <span>手机号</span>
                <div :class="{ 'has-error': fieldErrors.contactPhone }">
                  <Phone :size="18" />
                  <input
                    v-model="form.contactPhone"
                    name="contactPhone"
                    type="tel"
                    inputmode="numeric"
                    autocomplete="tel"
                    placeholder="请输入 11 位手机号"
                    :aria-invalid="Boolean(fieldErrors.contactPhone)"
                    @input="fieldErrors.contactPhone = undefined"
                  />
                </div>
                <small v-if="fieldErrors.contactPhone">{{ fieldErrors.contactPhone }}</small>
              </label>

              <label class="checkout-field">
                <span>邮箱</span>
                <div :class="{ 'has-error': fieldErrors.contactEmail }">
                  <Mail :size="18" />
                  <input
                    v-model="form.contactEmail"
                    name="contactEmail"
                    type="email"
                    autocomplete="email"
                    placeholder="name@example.com"
                    :aria-invalid="Boolean(fieldErrors.contactEmail)"
                    @input="fieldErrors.contactEmail = undefined"
                  />
                </div>
                <small v-if="fieldErrors.contactEmail">{{ fieldErrors.contactEmail }}</small>
              </label>
            </section>

            <label :class="['checkout-agreement', { 'has-error': fieldErrors.agreed }]">
              <input
                v-model="form.agreed"
                name="agreed"
                type="checkbox"
                @change="fieldErrors.agreed = undefined"
              />
              <span class="checkout-checkbox">
                <Check :size="13" stroke-width="3" />
              </span>
              <span>我已阅读并同意服务条款与隐私政策。</span>
            </label>
            <small v-if="fieldErrors.agreed" class="checkout-agreement-error">{{ fieldErrors.agreed }}</small>
          </form>
        </div>

        <aside class="checkout-summary" aria-label="订单信息">
          <div class="checkout-summary__top">
            <p>订单信息</p>
            <span>{{ selectedPlan.label }}</span>
          </div>
          <h2>{{ selectedPlan.name }}</h2>
          <p class="checkout-summary__period">{{ selectedPlan.period }}订阅</p>

          <ul>
            <li v-for="feature in selectedPlan.features" :key="feature">
              <Check :size="17" stroke-width="2.4" />
              <span>{{ feature }}</span>
            </li>
          </ul>

          <dl>
            <div>
              <dt>套餐价格</dt>
              <dd>{{ selectedPlan.price }}</dd>
            </div>
            <div>
              <dt>优惠</dt>
              <dd>¥0</dd>
            </div>
            <div class="checkout-summary__total">
              <dt>今日应付</dt>
              <dd>{{ selectedPlan.price }}</dd>
            </div>
          </dl>

          <button
            type="button"
            class="checkout-submit"
            :disabled="isSubmitting"
            @click="confirmOrder"
          >
            <LoaderCircle v-if="isSubmitting" class="checkout-spin" :size="18" />
            <LockKeyhole v-else :size="18" />
            {{ isSubmitting ? "正在创建订单" : "确认订单" }}
          </button>

          <p class="checkout-summary__note">
            <ShieldCheck :size="16" />
            创建订单后将前往 Z-Pay 完成支付。
          </p>
        </aside>
      </section>

      <section v-else class="checkout-empty">
        <h1>未找到可购买的套餐</h1>
        <p>请返回套餐页重新选择。</p>
        <button type="button" @click="returnToPricing">返回套餐页</button>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
