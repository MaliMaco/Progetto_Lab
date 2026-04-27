from typing import Dict, Counter
from collections import Counter


class TokenEvaluator:
    
    '''
    Modulo contenente la classe che si occupa di generare le metriche di valutazione
    per la correttezza del crawler. Implementa vari metodi statici utili a pulire i testi
    da caratteri invisibili e di formattazione ed a trasformare i testi in strutture dati
    utili alle operazioni insiemistiche necessarie per calcolare le metriche di valutazione.
    '''

    @staticmethod
    def normalize(text: str) -> str:

        '''
        Prima pulizia.
        '''

        text = text.strip()
        return text

    @staticmethod
    def token_parsed_text(parsed_text: str) -> Counter[str]:

        '''
        Trasforma il testo parsato dal crawler in un Multi-Insieme contentente ogni suo token.
        '''

        cleaned_tokens = TokenEvaluator.normalize(parsed_text)
        tokens = cleaned_tokens.strip().split()
        parsed_tokens = Counter(tokens)
        return parsed_tokens

    @staticmethod
    def token_gold_text(gold_text: str) -> Counter[str]:

        '''
        Trasforma il golden text in un Multi-Insieme contentente ogni suo token.
        '''

        cleaned_tokens = TokenEvaluator.normalize(gold_text)
        tokens = cleaned_tokens.strip().split()
        parsed_tokens = Counter(tokens)
        return parsed_tokens

    @staticmethod
    def evaluate(parsed_text: Counter[str], gold_text: Counter[str]) -> Dict[str,float]:

        '''
        Effettiva funzione che calcola le metriche di valutazione come specificato dai professori. 
        Affronta l'edge case in cui l'intersezione di gold text e parsed text genera un insieme vuoto.
        Precision rappresenta il numero corretto di token presenti tra quelli trovati dal modello.
        Recall rappresenta il numero di token corretti che il modello è effettivamente riuscito a trovare.
        F1 è la media armonica tra precision e recall, è un buon indicatore di correttezza.
        '''

        intersect = parsed_text & gold_text
        intersection_length = sum(intersect.values())
        parsed_length = sum(parsed_text.values())
        gold_length = sum(gold_text.values())
        precision = intersection_length/parsed_length if parsed_length > 0 else 0.0
        recall = intersection_length/gold_length if gold_length > 0 else 0.0
        denom = (precision+recall)
        f1 = 2*precision*recall/denom if denom > 0 else 0.0
        return {
                "precision": precision,
                "recall": recall,
                "f1": f1
            }