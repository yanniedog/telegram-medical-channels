from discover_channels import TG_HANDLE
text = open("lyzem_sample.html", encoding="utf-8").read()
print("null bytes", text.count("\x00"))
portion = text[10000:12000]
print("portion matches", len(list(TG_HANDLE.finditer(portion))))
print("full matches", len(list(TG_HANDLE.finditer(text))))
# try simpler pattern
import re
simple = re.compile(r"t\.me/([A-Za-z0-9_]+)")
print("simple full", len(simple.findall(text)))
