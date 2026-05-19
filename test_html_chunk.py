from discover_channels import TG_HANDLE
text = open("lyzem_sample.html", encoding="utf-8").read()
idx = text.find("bookstoread_pdf")
print("idx", idx)
chunk = text[idx-30:idx+30]
print(repr(chunk))
print("findall", TG_HANDLE.findall(chunk))
print("all matches", len(list(TG_HANDLE.finditer(text))))
