"use client";

import type { PermissionCatalog } from "@/lib/types";

/** What a person may open. Presets fill the list in one click; managing a section automatically includes looking at it. */
export function PermissionPicker({ catalog, value, onChange }: { catalog: PermissionCatalog; value: string[]; onChange: (keys: string[]) => void }) {
  const selected = new Set(value);

  function toggle(key: string) {
    const next = new Set(selected);
    if (next.has(key)) {
      next.delete(key);
      for (const entry of catalog.entries) if (entry.implies === key) next.delete(entry.key);
    } else {
      next.add(key);
      const implied = catalog.entries.find((entry) => entry.key === key)?.implies;
      if (implied) next.add(implied);
    }
    onChange([...next]);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-bold text-fg-muted">آماده:</span>
        {catalog.presets.map((preset) => (
          <button key={preset.key} type="button" onClick={() => onChange(preset.permissions)} className="rounded-full border border-line-strong px-3 py-1.5 text-sm font-bold hover:bg-surface-2">
            {preset.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => onChange(catalog.entries.filter((entry) => entry.default_for_staff).map((entry) => entry.key))}
          className="rounded-full border border-line-strong px-3 py-1.5 text-sm font-bold hover:bg-surface-2"
        >
          پیش‌فرض کارمند
        </button>
        <button type="button" onClick={() => onChange([])} className="rounded-full border border-line-strong px-3 py-1.5 text-sm font-bold hover:bg-surface-2">
          هیچ‌کدام
        </button>
      </div>
      <ul className="grid gap-2 md:grid-cols-2">
        {catalog.entries.map((entry) => (
          <li key={entry.key}>
            <label className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-3 transition-colors ${selected.has(entry.key) ? "border-ink bg-surface-2" : "border-line"}`}>
              <input type="checkbox" className="mt-1 h-5 w-5 accent-[#0c0d10]" checked={selected.has(entry.key)} onChange={() => toggle(entry.key)} />
              <span>
                <span className="block font-black">{entry.label}</span>
                <span className="block text-xs leading-6 text-fg-muted">{entry.description}</span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      <p className="text-xs leading-6 text-fg-subtle">مدیریت کاربران فقط برای مالک است و به کسی داده نمی‌شود. بخش‌هایی که فعال نباشد در منوی آن شخص دیده نمی‌شود و سرور هم درخواستش را رد می‌کند.</p>
    </div>
  );
}
