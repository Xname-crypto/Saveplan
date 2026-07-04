# `@edgespark/web`

EdgeSpark browser SDK.

This package is intentionally:

- browser-only
- same-origin only
- cookie-session only
- zero-config
- optimized for agent-written code

Recommended browser auth path:

- use `@edgespark/web` for all browser auth
- prefer `authUI.mount()` for managed auth UI
- use `es.auth` for custom flows
- do not implement app auth by calling `/api/_es/auth/*` manually

## Use in this repo

```bash
pnpm install
pnpm --filter @edgespark/web build
```

## Quick start

```ts
import { createEdgeSpark } from "@edgespark/web";
import "@edgespark/web/styles.css";

const es = createEdgeSpark();
const container = document.getElementById("auth")!;

es.authUI.mount(container, {
  redirectTo: "/dashboard",
});
```

Auto-detected labels are used by default. The managed UI picks the best preset
from the browser's language preferences automatically.

## Public surface

```ts
const es = createEdgeSpark();
const container = document.getElementById("auth")!;

es.auth;
es.api.fetch("/api/todos");
es.authUI.mount(container, { redirectTo: "/dashboard" });
```

### `auth`

`es.auth` keeps better-auth's API shape and adds two EdgeSpark helpers:

```ts
const session = await es.auth.requireSession();

const unsubscribe = es.auth.onSessionChange((nextSession) => {
  console.log(nextSession?.user.email ?? "signed out");
});
```

`requireSession()` throws `UNAUTHENTICATED` only when no session exists. If the
session lookup itself fails, it preserves the upstream auth error code/status
so route guards can distinguish backend failures from a real sign-out.

`onSessionChange()` is hydration-safe: it waits for the first session lookup to
complete before emitting, so apps do not mistake initial loading for a real
signed-out state. Successful sign-in/sign-up/sign-out mutations also prompt
other tabs to refetch their session state.

Current platform note:
- `changeEmail()`
- `deleteUser()`
- `deleteUserCallback()`

still appear on the familiar better-auth-shaped surface, but EdgeSpark does
not currently enable those platform capabilities. These methods fail fast with
`UNSUPPORTED_AUTH_METHOD`. For normal browser auth flows, stay on the supported
paths: `authUI.mount()` for managed UI and `es.auth` for supported custom flows.

Use the familiar auth methods directly:

```ts
await es.auth.signIn.email({ email, password });
await es.auth.signUp.email({ name, email, password });
await es.auth.signOut();
await es.auth.getSession();
```

The platform-managed `/api/_es/auth/*` routes exist underneath the SDK, but normal app code should not call them directly. Treat those routes as implementation details unless you are debugging auth at the HTTP layer.

### `api`

`es.api.fetch(...)` is the same-origin fetch wrapper for authenticated app requests.

```ts
const response = await es.api.fetch("/api/todos");
const todos = await response.json();
```

The wrapper always uses cookie credentials, rejects cross-origin URLs, and does not accept a `credentials` override in its `init` type.

### `authUI`

The managed auth UI supports exactly two post-auth strategies.

#### Redirect mode

```ts
const container = document.getElementById("auth")!;

const ui = es.authUI.mount(container, {
  redirectTo: "/dashboard",
});
```

#### Controlled mode

```ts
const container = document.getElementById("auth")!;

const ui = es.authUI.mount(container, {
  onSuccess(event) {
    if (event.action === "password-reset") {
      return;
    }

    window.location.assign("/dashboard");
  },
});
```

`ui.destroy()` removes the mounted UI and clears timers/listeners.

`onError` always receives a normalized `EdgeSparkAuthError`, so callback code
can safely read `error.code`, `error.message`, and `error.status` without
defensive `unknown` handling.

```ts
es.authUI.mount(container, {
  onSuccess(event) {
    if (event.action !== "password-reset") {
      window.location.assign("/dashboard");
    }
  },
  onError(error) {
    console.error(error.code, error.message);
  },
});
```

Password reset has one special rule:

- in controlled mode, `onSuccess({ action: "password-reset" })` fires and the caller owns the next step
- in redirect mode, the UI returns to sign-in with a success notice instead of redirecting to an authenticated page
- if the platform keeps JWT session cookie cache enabled, reset-time session revocation remains eventually consistent for already-open browser contexts and may take up to the cache TTL to become visible

In controlled mode, `authUI` stops mutating the container after `onSuccess`
runs. If the app wants to close, replace, or reuse that container, it owns that
teardown explicitly.

#### Appearance

Managed auth supports a small, explicit appearance contract. If `appearance` is
omitted, the UI keeps its built-in default styling.

- `theme` selects the built-in starting preset
- `variables` override specific design tokens on top of that preset
- `className` adds a stable root hook for app-scoped CSS

```ts
import {
  AUTH_UI_APPEARANCE_VARIABLE,
  AUTH_UI_THEME,
  type AuthUIAppearance,
} from "@edgespark/web";

const appearance = {
  theme: AUTH_UI_THEME.DARK,
  className: "my-auth-surface",
  variables: {
    [AUTH_UI_APPEARANCE_VARIABLE.PRIMARY]: "#d97d4a",
    [AUTH_UI_APPEARANCE_VARIABLE.FONT]: '"Manrope", sans-serif',
  },
} satisfies AuthUIAppearance;

es.authUI.mount(container, {
  redirectTo: "/dashboard",
  appearance,
});
```

Supported appearance fields:

- `theme`: `"light"` or `"dark"` (`"light"` is the default)
- `className`: applied to the managed auth UI root container
- `variables`: stable CSS custom properties for light-touch theming

`appearance.variables` are applied as inline CSS custom properties on the
managed auth root, so explicit overrides win over the built-in stylesheet
defaults without requiring consumers to manage CSS load order.

When the appearance object is assigned to a variable before calling
`authUI.mount(...)`, prefer `satisfies AuthUIAppearance` so `tsc` rejects
unsupported theme values, unsupported token keys, and misspelled appearance
fields during type-checking.

Supported `appearance.variables` keys:

| Variable | Controls | Light default |
|----------|----------|---------------|
| `--edgespark-auth-bg` | Page/input background, status mix base | `#ffffff` |
| `--edgespark-auth-bg-muted` | Secondary button hover, muted status bg, modal close hover | `#f7f7f8` |
| `--edgespark-auth-card-bg` | Card background (accepts gradient or flat color) | `linear-gradient(180deg, #ffffff, #fcfcfc)` |
| `--edgespark-auth-border` | Input border, secondary button border, divider line | `rgba(15,23,42,0.08)` |
| `--edgespark-auth-text` | All body text | `#111827` |
| `--edgespark-auth-text-muted` | Subtitles, meta text, divider label, modal close icon | `#6b7280` |
| `--edgespark-auth-divider-bg` | Divider pill background (masks the line behind the label) | inherits `--edgespark-auth-bg` |
| `--edgespark-auth-primary` | Primary button bg, links, input focus ring + border | `#0f766e` |
| `--edgespark-auth-primary-hover` | Primary button hover bg | `#115e59` |
| `--edgespark-auth-primary-contrast` | Primary button text | `#ffffff` |
| `--edgespark-auth-error` | Error status text + tinted bg | `#b91c1c` |
| `--edgespark-auth-info` | Info status text + tinted bg | `#0f766e` |
| `--edgespark-auth-radius-card` | Card border radius | `20px` |
| `--edgespark-auth-radius-control` | Input border radius | `12px` |
| `--edgespark-auth-shadow` | Card box shadow | `0 24px 60px rgba(15,23,42,0.08)` |
| `--edgespark-auth-font` | Root font family | `"IBM Plex Sans", "Inter", ui-sans-serif, system-ui, sans-serif` |
| `--edgespark-auth-modal-backdrop` | OAuth modal overlay background | `rgba(15,23,42,0.22)` |
| `--edgespark-auth-modal-card-bg` | OAuth modal card background | `#ffffff` |
| `--edgespark-auth-modal-shadow` | OAuth modal card box shadow | `0 24px 60px rgba(15,23,42,0.18)` |

Only the root container hook, the theme attribute, and the documented CSS
variables above are part of the managed auth appearance contract. Internal
`.edgespark-auth__*` classes remain implementation details and should not be
treated as a stable public API.

## Flows covered by the managed UI

- email/password sign-in
- email/password sign-up
- OAuth sign-in
- email verification instructions + resend
- forgot password
- reset password with email OTP

The forgot-password path only appears when the project config enables email-OTP password reset.

## Locale presets

Managed auth UI labels auto-detect by default, so most apps do not need to
import locale helpers manually.

Import a preset only when the app wants to force a specific language or build
on top of a known base:

```ts
import { createEdgeSpark, fr } from "@edgespark/web";

const es = createEdgeSpark();

es.authUI.mount(container, {
  redirectTo: "/dashboard",
  labels: fr,
});
```

`detectLocale()` is exported for advanced cases that want the same browser
language matching outside the managed auth UI.

## Design notes

- `createEdgeSpark()` takes no options
- current page origin is used internally
- auth base path is internal
- credentials mode is internal
- local dev with separate web/backend ports should use a dev proxy so the browser still sees same-origin requests
