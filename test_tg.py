from discover_channels import TG_HANDLE
print(repr(TG_HANDLE.pattern))
import re
p = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z0-9_]{4,})(?:/|\?|$)", re.I)
print("fresh", p.findall("https://t.me/bookstoread_pdf"))
print("imported", TG_HANDLE.findall("https://t.me/bookstoread_pdf"))
