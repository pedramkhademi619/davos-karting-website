"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigation } from "@/content/site";

type NavLinksProps = {
  className?: string;
  linkClassName?: string;
  onNavigate?: () => void;
};

/** Client component only because it needs the current path to mark the active page (aria-current). */
export function NavLinks({ className, linkClassName, onNavigate }: NavLinksProps) {
  const pathname = usePathname();
  return (
    <ul className={className}>
      {navigation.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <li key={item.href}>
            <Link href={item.href} aria-current={active ? "page" : undefined} className={linkClassName} onClick={onNavigate}>
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
