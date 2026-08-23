export const AUTH_PASSWORD_MIN_LENGTH = 8

export interface PasswordPolicyCheck {
  key: "length" | "letter" | "number"
  label: string
  ok: boolean
}

export function getPasswordPolicyChecks(password: string): PasswordPolicyCheck[] {
  return [
    {
      key: "length",
      label: `至少 ${AUTH_PASSWORD_MIN_LENGTH} 位`,
      ok: password.length >= AUTH_PASSWORD_MIN_LENGTH,
    },
    {
      key: "letter",
      label: "包含字母",
      ok: /[A-Za-z]/.test(password),
    },
    {
      key: "number",
      label: "包含数字",
      ok: /\d/.test(password),
    },
  ]
}

export function isStrongPassword(password: string) {
  return getPasswordPolicyChecks(password).every((check) => check.ok)
}

export function getPasswordStrengthLabel(password: string) {
  const score = getPasswordPolicyChecks(password).filter((check) => check.ok).length

  if (score === 3) return "强"
  if (score === 2) return "中"
  return "弱"
}

export function getPasswordPolicyMessage() {
  return `密码至少 ${AUTH_PASSWORD_MIN_LENGTH} 位，并且要同时包含字母和数字。`
}
