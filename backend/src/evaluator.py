from typing import Dict

class TokenEvaluator:

    @staticmethod
    def token_parsed_text(parsed_text: str) -> set[str]:
        tokens = parsed_text.split(" ")
        parsed_tokens = set()
        for token in tokens:
            parsed_tokens.add(token)
        return parsed_tokens

    @staticmethod
    def token_gold_text(gold_text: str) -> set[str]:
        tokens = gold_text.split(" ")
        parsed_tokens = set()
        for token in tokens:
            parsed_tokens.add(token)
        return parsed_tokens

    @staticmethod
    def evaluate(parsed_text: set[str], gold_text: set[str]) -> Dict[str,Dict[int]]:
        intersect = parsed_text.intersection(gold_text)
        intersect_length = len(intersect)
        parsed_length = len(parsed_text)
        gold_length = len(gold_text)
        precision = intersect_length/parsed_length
        recall = intersect_length/gold_length
        f1 = 2*precision*(recall/(precision+recall))
        return {
            "token_level_eval": {
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
        }