import json
import os
import re
import unicodedata

#Cambiare i nomi dei file in cui si trovano l'html ed il gs
html_file = open(os.path.join(os.path.dirname(__file__),"html_ecb_ben.txt"), "r", encoding="UTF-8")
gs_file = open(os.path.join(os.path.dirname(__file__),"gs1_GS.txt"), "r", encoding="UTF-8")

html_text = html_file.read()
gs_text = gs_file.read()

gs_text = unicodedata.normalize('NFKC', gs_text)
gs_text = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", gs_text)
gs_text = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', gs_text)
gs_text = re.sub(r'[\u2013\u2014\u2015]', '-', gs_text)
gs_text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u20AC\u00e8]', '', gs_text)
gs_text = re.sub(r'(?<=[^\s])\u00f9(?=[A-ZÀÈÉÌÒÙ])', ' ', gs_text)
gs_text = re.sub(r'\s+', ' ', gs_text).strip()

pattern_title = r'<(?:title|(?:div\s+class=["\'](?:title|header)["\'][^>]*>\s*<h[1-6]))[^>]*>\s*(?:<[^>]+>)?\s*(.*?)\s*(?:</[^>]+>)?\s*</(?:title|h[1-6])>'
match = re.search(pattern_title, html_text)
title = match.group(1)
title = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", title)
title = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', title)
title = re.sub(r'[\u2013\u2014\u2015]', '-', title)
title = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u20AC\u00e8]', '', title)
title = re.sub(r'(?<=[^\s])\u00f9(?=[A-ZÀÈÉÌÒÙ])', ' ', title)

pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
match = re.search(pattern_domain, "https://www.ecb.europa.eu/mopo/intro/benefits/html/index.it.html")
domain = match.group(1)

json_entry = {
    "url": "https://www.ecb.europa.eu/mopo/intro/benefits/html/index.it.html",
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
