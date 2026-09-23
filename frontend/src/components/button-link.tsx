import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowLeftIcon } from "@/components/icons";

type Variant = "primary" | "ghost" | "dark";
type Size = "sm" | "md" | "lg";

const base =
  "group inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-bold transition-all duration-300 ease-out-expo active:scale-[0.98]";

const variants: Record<Variant, string> = {
  primary: "bg-accent text-ink hover:bg-accent-hover hover:shadow-[0_14px_34px_-14px_rgb(190_130_0/0.8)]",
  ghost: "border border-fg text-fg hover:bg-fg hover:text-canvas",
  dark: "bg-ink text-white hover:bg-black hover:shadow-[0_14px_34px_-14px_rgb(0_0_0/0.6)]",
};

const sizes: Record<Size, string> = {
  sm: "h-10 px-5 text-sm",
  md: "h-12 px-7 text-base",
  lg: "h-14 px-9 text-lg",
};

type ButtonLinkProps = {
  href: string;
  children: ReactNode;
  variant?: Variant;
  size?: Size;
  arrow?: boolean;
  className?: string;
};

/** Internal paths use client-side navigation; anything else (e.g. the booking system) is a normal link. */
export function ButtonLink({ href, children, variant = "primary", size = "md", arrow = true, className = "" }: ButtonLinkProps) {
  const classes = `${base} ${variants[variant]} ${sizes[size]} ${className}`;
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
