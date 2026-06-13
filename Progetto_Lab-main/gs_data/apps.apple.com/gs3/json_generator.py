import json
import os
import re
import unicodedata
from bs4 import BeautifulSoup


html_file = open(os.path.join(os.path.dirname(__file__),"html_apple_instagram.txt"), "r", encoding="UTF-8")
gs_file = open(os.path.join(os.path.dirname(__file__),"gs3_GS.txt"), "r", encoding="UTF-8")

html_text = html_file.read()
gs_text = gs_file.read()

gs_text = unicodedata.normalize('NFKC', gs_text)
gs_text = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", gs_text)
gs_text = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', gs_text)
gs_text = re.sub(r'[\u2013\u2014\u2015]', '-', gs_text)
gs_text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u20AC\u00e8]', '', gs_text)
gs_text = re.sub(r'(?<=[^\s])\u00f9(?=[A-ZÀÈÉÌÒÙ])', ' ', gs_text)
gs_text = re.sub(r'\[\d+\]', '', gs_text)
gs_text = re.sub(r'\s+', ' ', gs_text).strip()

soup = BeautifulSoup(html_text, "html.parser")

title_tag = soup.find('title')
if title_tag:
    title = title_tag.get_text(strip=True)
else:
    div_title = soup.find('div', class_='title')
    title = div_title.get_text(strip=True) if div_title else "Nessun titolo"

url_list = "https://apps.apple.com/us/app/instagram/id389801252".split("/")
domain = url_list[2]

json_entry = {
    "url": "https://apps.apple.com/us/app/instagram/id389801252",
    "domain": domain,
    "title": title,
    "html_text":  html_text,
    "gold_text": gs_text
}


result = open(os.path.join(os.path.dirname(__file__),"gs3.json"), "w", encoding="UTF-8")
result.write(json.dumps(json_entry, indent=1))
result.close()
html_file.close()
gs_file.close()
