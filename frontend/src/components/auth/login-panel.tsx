"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { OtpLogin } from "@/components/auth/otp-login";

/** Only in-site paths are accepted as the destination after sign-in (no open redirects). */
function safeNext(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//") || raw.startsWith("/\\")) return "/account";
  return raw;
}

export function LoginPanel() {
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  return (
    <div className="panel mx-auto max-w-md p-7 md:p-9">
      <OtpLogin onSignedIn={() => router.replace(next)} />
    </div>
  );
}
