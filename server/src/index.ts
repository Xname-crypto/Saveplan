import { Hono, type Context } from "hono";
import { db, storage } from "edgespark";
import { eq, sql } from "drizzle-orm";
import { authSessions, authUsers, buckets, passwordResets } from "@defs";

const PBKDF2_ITERATIONS = 260_000;
const RESET_TOKEN_MINUTES = 60;
const SESSION_DAYS = 30;
const JWT_ALGORITHM = "HS256";
const JWT_SECRET = "saveplan-local-dev-jwt-secret";
const AUTH_VIDEO_KEYS = new Set(["login-visual.mp4", "register-visual.mp4", "fp_v3.mp4"]);
const textEncoder = new TextEncoder();

declare const btoa: (data: string) => string;
declare const atob: (data: string) => string;

type AuthUserRow = typeof authUsers.$inferSelect;
type JsonRecord = Record<string, unknown>;

class RequestError extends Error {
  constructor(
    public status: 400 | 401 | 409 | 422,
    message: string,
  ) {
    super(message);
  }
}

function utcNow() {
  return new Date();
}

function isoNow() {
  return utcNow().toISOString();
}

function sessionExpiresAt() {
  return new Date(utcNow().getTime() + SESSION_DAYS * 24 * 60 * 60 * 1000).toISOString();
}

function toHex(bytes: ArrayBuffer | Uint8Array) {
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  return Array.from(view, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function randomHex(byteLength: number) {
  const bytes = new Uint8Array(byteLength);
  crypto.getRandomValues(bytes);
  return toHex(bytes);
}

function parseInterests(value: string | null) {
  if (!value) return [];

  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string") : [];
  } catch (_error) {
    return [];
  }
}

function toUser(row: AuthUserRow) {
  return {
    id: row.id,
    email: row.email,
    username: row.username,
    job: row.job ?? undefined,
    bio: row.bio ?? undefined,
    interests: parseInterests(row.interests),
    avatar_name: row.avatarName ?? undefined,
    created_at: row.createdAt,
  };
}

function normalizeEmail(value: unknown) {
  const email = typeof value === "string" ? value.trim().toLowerCase() : "";
  if (!email || email.length > 254 || !email.includes("@") || !email.split("@").at(-1)?.includes(".")) {
    throw new RequestError(422, "请输入有效的邮箱地址。");
  }
  return email;
}

function requireText(payload: JsonRecord, key: string, min: number, max: number, message: string) {
  const value = payload[key];
  const text = typeof value === "string" ? value.trim() : "";
  if (text.length < min || text.length > max) {
    throw new RequestError(422, message);
  }
  return text;
}

function optionalText(payload: JsonRecord, key: string, max: number) {
  const value = payload[key];
  if (value === undefined || value === null) return null;
  if (typeof value !== "string") return null;
  const text = value.trim();
  return text.length > max ? text.slice(0, max) : text || null;
}

function getInterests(payload: JsonRecord) {
  const value = payload.interests;
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string").slice(0, 12);
}

async function hashPassword(password: string, saltHex = randomHex(16)) {
  const key = await crypto.subtle.importKey("raw", textEncoder.encode(password), "PBKDF2", false, [
    "deriveBits",
  ]);
  const salt = Uint8Array.from(saltHex.match(/.{1,2}/g) ?? [], (byte) => Number.parseInt(byte, 16));
  const digest = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      hash: "SHA-256",
      salt,
      iterations: PBKDF2_ITERATIONS,
    },
    key,
    256,
  );

  return {
    hash: toHex(digest),
    salt: saltHex,
  };
}

function constantTimeEqual(left: string, right: string) {
  if (left.length !== right.length) return false;

  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

async function verifyPassword(password: string, expectedHash: string, saltHex: string) {
  const { hash } = await hashPassword(password, saltHex);
  return constantTimeEqual(hash, expectedHash);
}

function base64urlEncode(bytes: Uint8Array) {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64urlDecode(value: string) {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (value.length % 4)) % 4);
  return Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
}

async function signJwtPart(signingInput: string) {
  const key = await crypto.subtle.importKey(
    "raw",
    textEncoder.encode(JWT_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, textEncoder.encode(signingInput));
  return base64urlEncode(new Uint8Array(signature));
}

async function createJwt(userId: string, tokenVersion: number) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: JWT_ALGORITHM, typ: "JWT" };
  const payload = {
    sub: userId,
    token_version: tokenVersion,
    iat: now,
    exp: now + SESSION_DAYS * 24 * 60 * 60,
  };
  const signingInput = [
    base64urlEncode(textEncoder.encode(JSON.stringify(header))),
    base64urlEncode(textEncoder.encode(JSON.stringify(payload))),
  ].join(".");
  return `${signingInput}.${await signJwtPart(signingInput)}`;
}

async function verifyJwt(token: string) {
  const [headerPart, payloadPart, signaturePart] = token.split(".");
  if (!headerPart || !payloadPart || !signaturePart) {
    throw new RequestError(401, "Session expired. Please sign in again.");
  }

  const signingInput = `${headerPart}.${payloadPart}`;
  if (!constantTimeEqual(signaturePart, await signJwtPart(signingInput))) {
    throw new RequestError(401, "Session expired. Please sign in again.");
  }

  try {
    const header = JSON.parse(new TextDecoder().decode(base64urlDecode(headerPart)));
    const payload = JSON.parse(new TextDecoder().decode(base64urlDecode(payloadPart)));

    if (header?.alg !== JWT_ALGORITHM || typeof payload?.sub !== "string" || typeof payload?.token_version !== "number") {
      throw new RequestError(401, "Session expired. Please sign in again.");
    }

    if (typeof payload.exp !== "number" || payload.exp < Math.floor(Date.now() / 1000)) {
      throw new RequestError(401, "Session expired. Please sign in again.");
    }

    return payload as { sub: string; token_version: number };
  } catch (error) {
    if (error instanceof RequestError) throw error;
    throw new RequestError(401, "Session expired. Please sign in again.");
  }
}

async function getJson(c: Context) {
  try {
    const payload = await c.req.json();
    return payload && typeof payload === "object" ? (payload as JsonRecord) : {};
  } catch (_error) {
    throw new RequestError(400, "请求格式不正确。");
  }
}

async function createSession(userId: string) {
  const token = randomHex(32);
  await db.insert(authSessions).values({
    token,
    userId,
    createdAt: isoNow(),
    expiresAt: sessionExpiresAt(),
  });
  return token;
}

async function getUserByBearerToken(authorization: string | undefined) {
  if (!authorization?.startsWith("Bearer ")) {
    throw new RequestError(401, "请先登录。");
  }

  const payload = await verifyJwt(authorization.replace("Bearer ", "").trim());
  const [row] = await db
    .select({
      id: authUsers.id,
      email: authUsers.email,
      username: authUsers.username,
      job: authUsers.job,
      bio: authUsers.bio,
      interests: authUsers.interests,
      avatarName: authUsers.avatarName,
      createdAt: authUsers.createdAt,
      passwordHash: authUsers.passwordHash,
      passwordSalt: authUsers.passwordSalt,
      tokenVersion: authUsers.tokenVersion,
    })
    .from(authUsers)
    .where(eq(authUsers.id, payload.sub))
    .limit(1);

  if (!row) {
    throw new RequestError(401, "登录状态已失效，请重新登录。");
  }

  if (row.tokenVersion !== payload.token_version) {
    throw new RequestError(401, "Session expired. Please sign in again.");
  }

  return row;
}

function handleError(error: unknown) {
  if (error instanceof RequestError) {
    return { detail: error.message, status: error.status };
  }

  console.error(error);
  return { detail: "请求失败，请稍后再试。", status: 500 as const };
}

const app = new Hono()
  .get("/api/public/health", (c) => c.json({ ok: true }))
  .get("/api/public/features", (c) =>
    c.json({
      auth: true,
      database: "edgespark",
    }),
  )
  .get("/api/public/media/auth-video/:filename", async (c) => {
    const filename = c.req.param("filename");

    if (!AUTH_VIDEO_KEYS.has(filename)) {
      return c.json({ detail: "Media not found." }, 404);
    }

    const { downloadUrl, expiresAt } = await storage
      .from(buckets.authMedia)
      .createPresignedGetUrl(`video/${filename}`, 60 * 60);

    return c.json({ downloadUrl, expiresAt: expiresAt.toISOString() });
  })
  .post("/api/public/auth/register", async (c) => {
    try {
      const payload = await getJson(c);
      const email = normalizeEmail(payload.email);
      const password = requireText(payload, "password", 6, 128, "密码至少需要 6 位。");
      const username = requireText(payload, "username", 3, 80, "昵称至少需要 3 个字符。");
      const job = requireText(payload, "job", 1, 120, "请输入职业或身份。");
      const bio = optionalText(payload, "bio", 600);
      const avatarName = optionalText(payload, "avatar_name", 255);
      const interests = getInterests(payload);
      const userId = crypto.randomUUID();
      const createdAt = isoNow();
      const { hash, salt } = await hashPassword(password);

      const [existing] = await db
        .select({ id: authUsers.id })
        .from(authUsers)
        .where(eq(authUsers.email, email))
        .limit(1);

      if (existing) {
        throw new RequestError(409, "这个邮箱已经注册过，请直接登录。");
      }

      const userRow: AuthUserRow = {
        id: userId,
        email,
        passwordHash: hash,
        passwordSalt: salt,
        username,
        job,
        bio,
        interests: JSON.stringify(interests),
        avatarName,
        tokenVersion: 0,
        createdAt,
      };

      await db.insert(authUsers).values(userRow);
      const token = await createJwt(userId, userRow.tokenVersion);

      return c.json({ token, user: toUser(userRow) }, 201);
    } catch (error) {
      const result = handleError(error);
      return c.json({ detail: result.detail }, result.status);
    }
  })
  .post("/api/public/auth/login", async (c) => {
    try {
      const payload = await getJson(c);
      const email = normalizeEmail(payload.email);
      const password = requireText(payload, "password", 1, 128, "请输入密码。");
      const [row] = await db.select().from(authUsers).where(eq(authUsers.email, email)).limit(1);

      if (!row || !(await verifyPassword(password, row.passwordHash, row.passwordSalt))) {
        throw new RequestError(401, "邮箱或密码不正确，请检查后重试。");
      }

      const token = await createJwt(row.id, row.tokenVersion);
      return c.json({ token, user: toUser(row) });
    } catch (error) {
      const result = handleError(error);
      return c.json({ detail: result.detail }, result.status);
    }
  })
  .post("/api/public/auth/forgot-password", async (c) => {
    try {
      const payload = await getJson(c);
      const email = normalizeEmail(payload.email);
      const message = "如果该邮箱已注册，重置链接已经生成。";
      const [row] = await db.select({ id: authUsers.id }).from(authUsers).where(eq(authUsers.email, email)).limit(1);

      if (!row) {
        return c.json({ message });
      }

      const token = randomHex(32);
      const expiresAt = new Date(utcNow().getTime() + RESET_TOKEN_MINUTES * 60 * 1000).toISOString();
      await db.delete(passwordResets).where(eq(passwordResets.userId, row.id));
      await db.insert(passwordResets).values({
        token,
        userId: row.id,
        expiresAt,
        createdAt: isoNow(),
      });

      const origin = c.req.header("origin") || new URL(c.req.url).origin;
      const resetUrl = `${origin}/reset-password?token=${token}`;
      return c.json({ message, reset_token: token, reset_url: resetUrl });
    } catch (error) {
      const result = handleError(error);
      return c.json({ detail: result.detail }, result.status);
    }
  })
  .post("/api/public/auth/reset-password", async (c) => {
    try {
      const payload = await getJson(c);
      const token = requireText(payload, "token", 16, 256, "重置链接无效或已经使用。");
      const password = requireText(payload, "password", 6, 128, "密码至少需要 6 位。");
      const [row] = await db.select().from(passwordResets).where(eq(passwordResets.token, token)).limit(1);

      if (!row) {
        throw new RequestError(400, "重置链接无效或已经使用。");
      }

      if (new Date(row.expiresAt) < utcNow()) {
        await db.delete(passwordResets).where(eq(passwordResets.token, token));
        throw new RequestError(400, "重置链接已过期，请重新发送。");
      }

      const { hash, salt } = await hashPassword(password);
      await db
        .update(authUsers)
        .set({
          passwordHash: hash,
          passwordSalt: salt,
          tokenVersion: sql`${authUsers.tokenVersion} + 1`,
        })
        .where(eq(authUsers.id, row.userId));
      await db.delete(passwordResets).where(eq(passwordResets.token, token));
      await db.delete(authSessions).where(eq(authSessions.userId, row.userId));

      return c.json({ message: "密码已更新。" });
    } catch (error) {
      const result = handleError(error);
      return c.json({ detail: result.detail }, result.status);
    }
  })
  .get("/api/public/auth/me", async (c) => {
    try {
      const user = await getUserByBearerToken(c.req.header("authorization"));
      return c.json(toUser(user));
    } catch (error) {
      const result = handleError(error);
      return c.json({ detail: result.detail }, result.status);
    }
  });

export default app;
