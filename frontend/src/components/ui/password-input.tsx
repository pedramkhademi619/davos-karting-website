"use client";

import { useState, type InputHTMLAttributes } from "react";
import { EyeIcon, EyeOffIcon } from "@/components/icons";

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { onDark?: boolean };

/** A password field with a button that shows or hides what was typed. */
export function PasswordInput({ className = "field", onDark = false, ...props }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <input {...props} type={visible ? "text" : "password"} dir="ltr" className={`${className} pr-12`} />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "پنهان کردن رمز عبور" : "نمایش رمز عبور"}
        aria-pressed={visible}
        className={`absolute right-3 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-full transition-colors ${onDark ? "text-on-carbon-muted hover:text-on-carbon" : "text-fg-subtle hover:text-fg"}`}
      >
        {visible ? <EyeOffIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
      </button>
    </div>
  );
}
