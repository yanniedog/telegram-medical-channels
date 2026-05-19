from discover_channels import TG_HANDLE
import re
text = open("lyzem_sample.html", encoding="utf-8").read()
idx = text.find("bookstoread_pdf")
chunk = text[idx-20:idx+20]
for i,c in enumerate(chunk):
    print(i, repr(c), ord(c))
url = "https://t.me/bookstoread_pdf"
print("direct", TG_HANDLE.findall(url))
# extract actual url from html
start = text.rfind("http", idx-30, idx)
end = text.find('"', start)
actual = text[start:end]
print("actual url repr", repr(actual))
print("actual matches", TG_HANDLE.findall(actual))
print("equal to plain?", actual == url)
