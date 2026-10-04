/** Persian names of what the assistant did with a question, in the order the owner reads them. */
export const OUTCOME_LABELS: Record<string, string> = {
  answered: "پاسخ از دانسته‌ها",
  quick_answer: "پاسخ سریع (بدون مدل)",
  small_talk: "سلام و تشکر",
  insufficient_information: "اطلاعات کافی نبود",
  refused_unsafe_input: "درخواست مشکوک رد شد",
  fallback_provider_unavailable: "مدل در دسترس نبود",
  fallback_budget_exhausted: "بودجهٔ روزانه تمام شد",
};

/** Outcomes that mean the customer did not get an answer: the ones worth reading. */
export const PROBLEM_OUTCOMES = ["insufficient_information", "fallback_provider_unavailable", "fallback_budget_exhausted"];

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  faq: "پرسش‌های متداول",
  policy: "قوانین",
  service: "خدمات",
  pricing: "قیمت",
  contact: "تماس",
};
