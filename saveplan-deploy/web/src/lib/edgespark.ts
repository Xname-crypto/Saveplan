/**
 * EdgeSpark client — singleton for auth + API.
 *
 * Usage:
 *   import { client } from "@/lib/edgespark"
 *
 *   // Auth (better-auth API — see https://www.better-auth.com/docs/client)
 *   await client.auth.signIn.email({ email, password })
 *   await client.auth.signUp.email({ name, email, password })
 *   const session = await client.auth.getSession()
 *
 *   // Managed login UI (renders into a container element)
 *   await client.auth.renderAuthUI(container, { redirectTo: "/dashboard" })
 *
 *   // API calls (fetch with auto-injected auth token)
 *   const res = await client.api.fetch("/api/users")
 *   const users = await res.json()
 */

import { createEdgeSpark } from "@edgespark/client";
import "@edgespark/client/styles.css";

export const client = createEdgeSpark();
