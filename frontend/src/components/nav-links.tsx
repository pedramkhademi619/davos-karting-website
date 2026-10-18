"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export type NavItem = { href: string; label: string };

type NavLinksProps = {
  items: readonly NavItem[];
  className?: string;
  linkClassName?: string;
  onNavigate?: () => void;
};

/** Client component only because it needs the current path to mark the active page (aria-current). */
export function NavLinks({ items, className, linkClassName, onNavigate }: NavLinksProps) {
  const pathname = usePathname();
  return (
    <ul className={className}>
      {items.map((item) => {
        // Links to the other host are absolute and never "current".
        const local = item.href.startsWith("/");
        const active = local && (item.href === "/" ? pathname === "/" : pathname.startsWith(item.href));
        return (
          <li key={item.label}>
            <Link href={item.href} aria-current={active ? "page" : undefined} className={linkClassName} onClick={onNavigate}>
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
