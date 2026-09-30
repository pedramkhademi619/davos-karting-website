"""Persian texts for providers that send plain messages (and for the development gateway)."""

from __future__ import annotations

_TEXTS = {
    "otp": "کد ورود شما به داوس کارتینگ: {code}\nاین کد را به هیچ‌کس ندهید.",
    "reservation_confirmed": (
        "{name}رزرو شما در داوس کارتینگ قطعی شد.\n"
        "کد بلیت: {ticket}\n"
        "{weekday} {date} ساعت {time}\n"
        "{karts}\n"
        "لطفا ۱۵ دقیقه زودتر برسید."
    ),
}


def render(template_key: str, parameters: dict[str, str]) -> str:
    if template_key == "custom":
        return parameters.get("text", "")
    template = _TEXTS.get(template_key)
    if template is None:
        raise KeyError(template_key)
    values = dict(parameters)
    if template_key == "reservation_confirmed":
        values["name"] = f"{values['name']} عزیز، " if values.get("name") else ""
    return template.format(**values)
