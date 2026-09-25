import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowLeftIcon } from "@/components/icons";

export type ButtonVariant = "primary" | "dark" | "ghost" | "ghost-light" | "signal";
export type ButtonSize = "sm" | "md" | "lg";

const base =
  "shine group inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-extrabold transition-all duration-300 ease-out-expo active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-ink shadow-[inset_0_-3px_0_rgb(0_0_0/0.12)] hover:bg-accent-hover hover:shadow-[0_16px_36px_-14px_rgb(255_176_0/0.9)]",
  dark: "bg-ink text-white hover:bg-black hover:shadow-[0_16px_36px_-14px_rgb(0_0_0/0.65)]",
  ghost: "border-2 border-fg text-fg hover:bg-fg hover:text-canvas",
  "ghost-light": "border-2 border-white/25 text-on-carbon hover:border-accent hover:text-accent",
  signal: "bg-signal text-white hover:shadow-[0_16px_36px_-14px_rgb(217_10_0/0.8)]",
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-10 px-5 text-sm",
  md: "h-12 px-7 text-base",
  lg: "h-14 px-9 text-lg",
};

export function buttonClasses(variant: ButtonVariant = "primary", size: ButtonSize = "md", extra = ""): string {
  return `${base} ${variants[variant]} ${sizes[size]} ${extra}`;
}

type ButtonLinkProps = {
  href: string;
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  arrow?: boolean;
  className?: string;
};

/** Internal paths use client-side navigation; anything else (phone, maps) is a normal link. */
export function ButtonLink({ href, children, variant = "primary", size = "md", arrow = true, className = "" }: ButtonLinkProps) {
  const classes = buttonClasses(variant, size, className);
  const content = (
    <>
      {children}
      {arrow && <ArrowLeftIcon className="h-5 w-5 transition-transform duration-300 group-hover:-translate-x-1" />}
    </>
  );

  if (href.startsWith("/")) {
    return (
      <Link href={href} className={classes}>
        {content}
      </Link>
    );
  }
  return (
    <a href={href} rel="noopener" className={classes}>
      {content}
    </a>
  );
}
