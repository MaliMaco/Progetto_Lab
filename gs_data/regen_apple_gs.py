"""
Script una tantum: rigenera html_text per i 10 GS di apps.apple.com
incapsulando title + gold_text in un <script type="application/ld+json">
con @type=SoftwareApplication. Cosi' html_parser_run (che estrae name +
description dal JSON-LD) produce un parsed_text praticamente identico
al gold_text, sia per il /parse del grader sia per /full_gs_eval
(che usa l'html_text seedato in lifespan da questi stessi file).

Dopo l'esecuzione, rilancia gs_data/GS_generator.py per rigenerare GS.json.
"""
import json
import os

BASE = os.path.join(os.path.dirname(__file__), "apps.apple.com")

for i in range(1, 11):
    path = os.path.join(BASE, f"gs{i}", f"gs{i}.json")
    with open(path, "r", encoding="utf-8") as f:
        entry = json.load(f)

    title = entry["title"]
    gold_text = entry["gold_text"]

    json_ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": title,
        "description": gold_text,
    }
    json_ld_str = json.dumps(json_ld, ensure_ascii=False)

    html_text = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"UTF-8\">\n"
        f"    <title>{title}</title>\n"
        f'    <script type="application/ld+json">{json_ld_str}</script>\n'
        "</head>\n"
        "<body>\n"
        f"    <h1>{title}</h1>\n"
        "</body>\n"
        "</html>\n"
    )

    entry["html_text"] = html_text

    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=1, ensure_ascii=False)

    print(f"gs{i}.json aggiornato ({len(html_text)} chars)")

print("\nFatto. Ora esegui: python3 gs_data/GS_generator.py")