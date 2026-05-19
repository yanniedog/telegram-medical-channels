import re
from discover_channels import TG_HANDLE
text = open("lyzem_sample.html", encoding="utf-8").read()
print(len(list(TG_HANDLE.finditer(text))))
