from django import template

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
