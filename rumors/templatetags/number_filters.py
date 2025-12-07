from django import template
from django.utils.timesince import timesince
from django.utils.timezone import now


register = template.Library()

@register.filter
def shorten_value(value):
    """
    Format angka besar jadi singkat dengan satuan:
    1000000 -> 1.0M
    25000000 -> 25.0M
    500000 -> 0.5M
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return value

    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"

@register.filter
def timesince_id(value):
    """
    Versi Bahasa Indonesia dari timesince, misal:
    '3 jam lalu', '5 hari lalu', dst.
    """
    if not value:
        return ""
    diff = timesince(value, now())
    diff = diff.replace("minutes", "menit").replace("minute", "menit")
    diff = diff.replace("hours", "jam").replace("hour", "jam")
    diff = diff.replace("days", "hari").replace("day", "hari")
    diff = diff.replace("weeks", "minggu").replace("week", "minggu")
    diff = diff.replace("months", "bulan").replace("month", "bulan")
    diff = diff.replace("years", "tahun").replace("year", "tahun")
    return f"{diff} lalu"

@register.filter
def translate_status(value):
    mapping = {
        "verified": "Terverifikasi",
        "pending": "Menunggu Verifikasi",
        "denied": "Ditolak",
    }
    return mapping.get(value.lower(), value)

@register.filter
def format_rupiah(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value  # kalau bukan angka, biarin aja

    # Format singkat berdasarkan besar nilai
    if value >= 1_000_000_000:
        formatted = f"{value / 1_000_000_000:.2f}".rstrip("0").rstrip(".") + "M"
    elif value >= 1_000_000:
        formatted = f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".") + "JT"
    elif value >= 1_000:
        formatted = f"{value:,.0f}".replace(",", ".")
    else:
        formatted = str(int(value))

    return f"Rp{formatted}"