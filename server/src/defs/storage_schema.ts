import type { BucketDef } from "@sdk/server-types";

export const authMedia: BucketDef<"auth-media"> = {
  bucket_name: "auth-media",
  description: "Authentication page videos",
};
