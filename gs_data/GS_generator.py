import json
import os

'''
Creatore del GS.json, il gold standard dell'intero dominio.
Facilmente espandibile con altri url se si vuole arricchire ulteriormente il test-set.
'''

lista = []

sito1_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs1/gs1.json"), "r", encoding="UTF-8")
sito2_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs2/gs2.json"), "r", encoding="UTF-8")
sito3_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs3/gs3.json"), "r", encoding="UTF-8")
sito4_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs4/gs4.json"), "r", encoding="UTF-8")
sito5_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs5/gs5.json"), "r", encoding="UTF-8")
sito6_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs6/gs6.json"), "r", encoding="UTF-8")
sito7_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs7/gs7.json"), "r", encoding="UTF-8")
sito8_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs8/gs8.json"), "r", encoding="UTF-8")
sito9_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs9/gs9.json"), "r", encoding="UTF-8")
sito10_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/gs10/gs10.json"), "r", encoding="UTF-8")

sito1_obj = json.load(sito1_json)
sito2_obj = json.load(sito2_json)
sito3_obj = json.load(sito3_json)
sito4_obj = json.load(sito4_json)
sito5_obj = json.load(sito5_json)
sito6_obj = json.load(sito6_json)
sito7_obj = json.load(sito7_json)
sito8_obj = json.load(sito8_json)
sito9_obj = json.load(sito9_json)
sito10_obj = json.load(sito10_json)

lista.append(sito1_obj)
lista.append(sito2_obj)
lista.append(sito3_obj)
lista.append(sito4_obj)
lista.append(sito5_obj)
lista.append(sito6_obj)
lista.append(sito7_obj)
lista.append(sito8_obj)
lista.append(sito9_obj)
lista.append(sito10_obj)

GS_json = open(os.path.join(os.path.dirname(__file__),"apps.apple.com/GS.json"), "w", encoding="UTF-8")
GS_json.write(json.dumps(lista, indent=1))

sito1_json.close()
sito2_json.close()
sito3_json.close()
sito4_json.close()
sito5_json.close()
sito6_json.close()
sito7_json.close()
sito8_json.close()
sito9_json.close()
sito10_json.close()