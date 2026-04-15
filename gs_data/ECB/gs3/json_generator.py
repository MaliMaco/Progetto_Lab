import json
import os
import re

#Cambiare i nomi dei file in cui si trovano l'html ed il gs
html_file = open(os.path.join(os.path.dirname(__file__),"gs3.html"), "r", encoding="UTF-8")
gs_file = open(os.path.join(os.path.dirname(__file__),"gs3_GS.txt"), "r", encoding="UTF-8")

html_text = html_file.read()
gs_text = gs_file.read()
pattern_title = r'<title>(.*?)</title>'
match = re.search(pattern_title, html_text)
title = match.group(1)
pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
match = re.search(pattern_domain, "https://www.ecb.europa.eu/paym/retail/retail_payments_strategy/html/index.en.html")
domain = match.group(1)


json_entry = {
    "url": "https://www.ecb.europa.eu/paym/retail/retail_payments_strategy/html/index.en.html",
    "domain": domain,
    "title": title,
    "html_text":  html_text,
    "gold_text": gs_text
}

#cambiare un nome sensato al file output, cmabiare nome per ogni pagina
result = open(os.path.join(os.path.dirname(__file__),"gs3.json"), "w", encoding="UTF-8")
result.write(json.dumps(json_entry, indent=1))
result.close()
html_file.close()
gs_file.close()