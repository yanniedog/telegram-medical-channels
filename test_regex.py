import re
from discover_channels import TG_HANDLE
text = open("lyzem_sample.html", encoding="utf-8").read()
print("len", len(text))
ms = list(TG_HANDLE.finditer(text))
print("matches", len(ms))
if ms: print([m.group(1) for m in ms[:10]])
# test single
s = 'href="https://t.me/bookstoread_pdf"'
print("single", TG_HANDLE.findall(s))
