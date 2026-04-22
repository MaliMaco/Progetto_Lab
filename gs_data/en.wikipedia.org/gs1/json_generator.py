import json
import os
import re
import unicodedata
from bs4 import BeautifulSoup

#Cambiare i nomi dei file in cui si trovano l'html ed il gs
html_file = open(os.path.join(os.path.dirname(__file__),"html_wiki_verilog.txt"), "r", encoding="UTF-8")
gs_file = open(os.path.join(os.path.dirname(__file__),"gs1_GS.txt"), "r", encoding="UTF-8")

html_text = html_file.read()
gs_text = gs_file.read()

gs_text = unicodedata.normalize('NFKC', gs_text)
gs_text = re.sub(r'\u00f9(?=[A-ZÀÈÉÌÒÙ])', ' ', gs_text)
gs_text = re.sub(r'[\u2018\u2019\u201a\u201b]', "'", gs_text)
gs_text = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', gs_text)
gs_text = re.sub(r'[\u2013\u2014\u2015]', '-', gs_text)
gs_text = re.sub(r'[\u00a0\u202f\u2009\u2008\u2007\u2006\u2005\u2004\u2003\u2002]', ' ', gs_text)
gs_text = re.sub(r'\s+', ' ', gs_text).strip()

soup = BeautifulSoup(html_text, "html.parser")

soup = BeautifulSoup(html_text, "html.parser")
title_tag = soup.find("h1", id="firstHeading") or soup.find("h1")
title = title_tag.get_text(strip=True) if title_tag else ""

pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
match = re.search(pattern_domain, "https://en.wikipedia.org/wiki/Verilog")
domain = match.group(1)

json_entry = {
    "url": "https://en.wikipedia.org/wiki/Verilog",
    "domain": domain,
    "title": title,
    "html_text":  html_text,
    "gold_text": gs_text
}

#cambiare un nome sensato al file output, cmabiare nome per ogni pagina
result = open(os.path.join(os.path.dirname(__file__),"gs1.json"), "w", encoding="UTF-8")
result.write(json.dumps(json_entry, indent=1))
result.close()
html_file.close()
gs_file.close()
