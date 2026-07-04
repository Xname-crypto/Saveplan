import { relations } from "drizzle-orm";
import { authSessions, authUsers, passwordResets } from "./db_schema";

export const authUsersRelations = relations(authUsers, ({ many }) => ({
  sessions: many(authSessions),
  passwordResets: many(passwordResets),
}));

export const authSessionsRelations = relations(authSessions, ({ one }) => ({
  user: one(authUsers, {
    fields: [authSessions.userId],
    references: [authUsers.id],
  }),
}));

export const passwordResetsRelations = relations(passwordResets, ({ one }) => ({
  user: one(authUsers, {
    fields: [passwordResets.userId],
    references: [authUsers.id],
  }),
}));
