import json
import os

'''
Creatore del GS.json, il gold standard dell'intero dominio.
Facilmente espandibile con altri url se si vuole arricchire ulteriormente il test-set.
'''

lista = []

sito1_json = open(os.path.join(os.path.dirname(__file__),"ECB/gs1/gs1.json"), "r", encoding="UTF-8")
sito2_json = open(os.path.join(os.path.dirname(__file__),"ECB/gs2/gs2.json"), "r", encoding="UTF-8")
sito3_json = open(os.path.join(os.path.dirname(__file__),"ECB/gs3/gs3.json"), "r", encoding="UTF-8")
sito4_json = open(os.path.join(os.path.dirname(__file__),"ECB/gs4/gs4.json"), "r", encoding="UTF-8")
sito5_json = open(os.path.join(os.path.dirname(__file__),"ECB/gs5/gs5.json"), "r", encoding="UTF-8")

sito1_obj = json.load(sito1_json)
sito2_obj = json.load(sito2_json)
sito3_obj = json.load(sito3_json)
sito4_obj = json.load(sito4_json)
sito5_obj = json.load(sito5_json)

lista.append(sito1_obj)
lista.append(sito2_obj)
lista.append(sito3_obj)
lista.append(sito4_obj)
lista.append(sito5_obj)

GS_json = open(os.path.join(os.path.dirname(__file__),"ECB/GS.json"), "w", encoding="UTF-8")
GS_json.write(json.dumps(lista, indent=1))

sito1_json.close()
sito2_json.close()
sito3_json.close()
sito4_json.close()
sito5_json.close()