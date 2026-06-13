import json
import os
import re
import unicodedata
from bs4 import BeautifulSoup

html_file = open(os.path.join(os.path.dirname(__file__),"html_ecb_c1e.txt"), "r", encoding="UTF-8")
gs_file = open(os.path.join(os.path.dirname(__file__),"gs4_GS.txt"), "r", encoding="UTF-8")

html_text = html_file.read()
gs_text = gs_file.read()

gs_text = unicodedata.normalize('NFKC', gs_text)
gs_text = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", gs_text)
gs_text = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', gs_text)
gs_text = re.sub(r'[\u2013\u2014\u2015]', '-', gs_text)
gs_text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u20AC\u00e8]', '', gs_text)
gs_text = re.sub(r'(?<=[^\s])\u00f9(?=[A-ZÀÈÉÌÒÙ])', ' ', gs_text)
gs_text = re.sub(r'\s+', ' ', gs_text).strip()

soup = BeautifulSoup(html_text, "html.parser")
title_tag = soup.find("h1", id="firstHeading") or soup.find("h1")
title = title_tag.get_text(strip=True) if title_tag else ""

url_list = "https://www.ecb.europa.eu/euro/coins/1euro/html/index.it.html".split("/")
domain = url_list[2]


json_entry = {
    "url": "https://www.ecb.europa.eu/euro/coins/1euro/html/index.it.html",
    "domain": domain,
    "title": title,
    "html_text":  html_text,
    "gold_text": gs_text
}


result = open(os.path.join(os.path.dirname(__file__),"gs4.json"), "w", encoding="UTF-8")
result.write(json.dumps(json_entry, indent=1))
result.close()
html_file.close()
gs_file.close()
