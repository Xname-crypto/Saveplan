export type PlanId = "starter" | "rescue-monthly" | "elite-yearly"

export interface PlanDefinition {
  id: PlanId
  name: string
  label: string
  price: string
  priceFen: number
  period: string
  cta: string
  featured: boolean
  purchasable: boolean
  features: string[]
}

export const plans: PlanDefinition[] = [
  {
    id: "starter",
    name: "新手启航",
    label: "Starter",
    price: "¥0",
    priceFen: 0,
    period: "/月",
    cta: "开始免费使用",
    featured: false,
    purchasable: false,
    features: ["每日 5 次转换", "基础校对", "导出 PDF"],
  },
  {
    id: "rescue-monthly",
    name: "高效抢救",
    label: "Popular",
    price: "¥29",
    priceFen: 2900,
    period: "/月",
    cta: "立即升级",
    featured: true,
    purchasable: true,
    features: ["无限次转换", "AI 智能纠错", "导出 Anki / Markdown", "云端自动同步"],
  },
  {
    id: "elite-yearly",
    name: "学术精英",
    label: "Exclusive",
    price: "¥199",
    priceFen: 19900,
    period: "/年",
    cta: "获取年度特惠",
    featured: false,
    purchasable: true,
    features: ["包含 Pro 全部功能", "专属模板库", "优先 AI 解析通道", "1 对 1 技术支持"],
  },
]

export function getPlanById(planId: string | undefined) {
  return plans.find((plan) => plan.id === planId)
}
