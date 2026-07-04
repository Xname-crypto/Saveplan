ALTER TABLE `auth_sessions` ADD COLUMN `expires_at` text;
--> statement-breakpoint
UPDATE `auth_sessions` SET `expires_at` = datetime('now', '+30 days') WHERE `expires_at` IS NULL;
