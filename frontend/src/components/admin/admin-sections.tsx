import type { ComponentType, SVGProps } from "react";
import { AccountingTab } from "@/components/admin/accounting/accounting-tab";
import { AssistantTab } from "@/components/admin/assistant-tab";
import { CustomersTab } from "@/components/admin/customers-tab";
import { DashboardTab } from "@/components/admin/dashboard-tab";
import { GuideTab } from "@/components/admin/guide-tab";
import { PaymentsTab } from "@/components/admin/payments-tab";
import { ReservationsTab } from "@/components/admin/reservations-tab";
import { SettingsTab } from "@/components/admin/settings-tab";
import { SmsTab } from "@/components/admin/sms-tab";
import { SystemStatusTab } from "@/components/admin/system-status-tab";
import { UsersTab } from "@/components/admin/users-tab";
import { BookIcon, CalendarIcon, CardIcon, ChatIcon, GaugeIcon, PulseIcon, SettingsIcon, SmsIcon, UserIcon, UsersIcon } from "@/components/icons";

export type SectionKey = "dashboard" | "reservations" | "customers" | "payments" | "sms" | "assistant" | "settings" | "accounting" | "system" | "users" | "guide";

export type Section = {
  key: SectionKey;
  label: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  /** The permission needed to open it (the same key the API checks), "owner" for the owner only, or "any" for every signed-in staff member. */
  permission: string;
  Component: ComponentType<{ onOpen: (key: SectionKey) => void }>;
};

/**
 * Every section of the admin panel, in menu order. To add one: add its permission on the server (AdminPermission and
 * PermissionCatalog), protect its API routes with require_permission, and add one row here.
 */
export const SECTIONS: Section[] = [
  { key: "dashboard", label: "داشبورد", icon: GaugeIcon, permission: "dashboard", Component: DashboardTab },
  { key: "reservations", label: "رزروها و سانس‌ها", icon: CalendarIcon, permission: "reservations", Component: ReservationsTab },
  { key: "customers", label: "مشتریان", icon: UserIcon, permission: "customers", Component: CustomersTab },
  { key: "payments", label: "پرداخت‌ها", icon: CardIcon, permission: "payments", Component: PaymentsTab },
  { key: "sms", label: "پنل پیامک", icon: SmsIcon, permission: "sms", Component: SmsTab },
  { key: "assistant", label: "دستیار هوشمند", icon: ChatIcon, permission: "assistant", Component: AssistantTab },
  { key: "settings", label: "تنظیمات و قیمت‌ها", icon: SettingsIcon, permission: "settings", Component: SettingsTab },
  { key: "accounting", label: "حسابداری", icon: BookIcon, permission: "accounting", Component: AccountingTab },
  { key: "system", label: "وضعیت سرویس‌ها", icon: PulseIcon, permission: "system", Component: SystemStatusTab },
  { key: "users", label: "کاربران پنل", icon: UsersIcon, permission: "owner", Component: UsersTab },
  { key: "guide", label: "راهنمای پنل", icon: ChatIcon, permission: "any", Component: GuideTab },
];

export function sectionAllowed(section: Section, can: (permission: string) => boolean, isOwner: boolean): boolean {
  if (section.permission === "any") return true;
  return section.permission === "owner" ? isOwner : can(section.permission);
}
