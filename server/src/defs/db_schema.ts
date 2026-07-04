import { sql } from "drizzle-orm";
import { index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const authUsers = sqliteTable(
  "auth_users",
  {
    id: text("id").primaryKey(),
    email: text("email").notNull().unique(),
    passwordHash: text("password_hash").notNull(),
    passwordSalt: text("password_salt").notNull(),
    username: text("username").notNull(),
    job: text("job"),
    bio: text("bio"),
    interests: text("interests").notNull().default("[]"),
    avatarName: text("avatar_name"),
    tokenVersion: integer("token_version").notNull().default(0),
    createdAt: text("created_at").notNull().default(sql`(current_timestamp)`),
  },
);

export const authSessions = sqliteTable(
  "auth_sessions",
  {
    token: text("token").primaryKey(),
    userId: text("user_id")
      .notNull()
      .references(() => authUsers.id, { onDelete: "cascade" }),
    createdAt: text("created_at").notNull().default(sql`(current_timestamp)`),
    expiresAt: text("expires_at").notNull(),
  },
  (table) => [index("auth_sessions_user_id_idx").on(table.userId)],
);

export const passwordResets = sqliteTable(
  "password_resets",
  {
    token: text("token").primaryKey(),
    userId: text("user_id")
      .notNull()
      .references(() => authUsers.id, { onDelete: "cascade" }),
    expiresAt: text("expires_at").notNull(),
    createdAt: text("created_at").notNull().default(sql`(current_timestamp)`),
  },
  (table) => [index("password_resets_user_id_idx").on(table.userId)],
);
