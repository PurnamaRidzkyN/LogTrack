from datetime import datetime


def timesince(value):

    if not value:
        return "-"

    # Kalau dari SQLite string
    if isinstance(value, str):
        value = datetime.strptime(
            value,
            "%Y-%m-%d %H:%M:%S"
        )

    now = datetime.now()
    diff = now - value

    seconds = diff.total_seconds()

    if seconds < 60:
        return "Baru saja"

    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} menit lalu"

    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} jam lalu"

    elif seconds < 2592000:
        days = int(seconds // 86400)
        return f"{days} hari lalu"

    return value.strftime("%d %b %Y")