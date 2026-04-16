import json

#Cambiare i nomi dei file in cui si trovano l'html ed il gs
html_file = open("./ECB/gs1/gs1.html", "r", encoding="UTF-8")
gs_file = open("./ECB/gs1/gs1_GS.txt", "r", encoding="UTF-8")

html_text = html_file.read()
gs_text = gs_file.read()


json_entry = {
    '''Cambiare i dati per url, dominio e titolo in modo da creare i singoli GS per i vari domini'''
    "url": "https://www.ecb.europa.eu/mopo/intro/benefits/html/index.it.html",
    "domain": "en.wikipedia.org",
    "title": "Benefits of price stability",
    "html_text":  html_text,
    "gold_text": gs_text
}

#cambiare un nome sensato al file output, cmabiare nome per ogni pagina
result = open("./ECB/gs1/gs1.json", "w", encoding="UTF-8")
result.write(json.dumps(json_entry, indent=1))
html_file.close()
gs_file.close()