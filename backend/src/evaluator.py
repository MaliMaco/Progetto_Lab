from typing import Dict, Set

class TokenEvaluator:

    @staticmethod
    def token_parsed_text(parsed_text: str) -> Set[str]:
        tokens = parsed_text.split(" ")
        parsed_tokens = set()
        for token in tokens:
            parsed_tokens.add(token)
        return parsed_tokens

    @staticmethod
    def token_gold_text(gold_text: str) -> Set[str]:
        tokens = gold_text.split(" ")
        parsed_tokens = set()
        for token in tokens:
            parsed_tokens.add(token)
        return parsed_tokens

    @staticmethod
    def evaluate(parsed_text: Set[str], gold_text: Set[str]) -> Dict[str,float]:
        intersect = parsed_text.intersection(gold_text)
        intersection_length = len(intersect)
        parsed_length = len(parsed_text)
        gold_length = len(gold_text)
        precision = intersection_length/parsed_length if parsed_length > 0 else 0.0
        recall = intersection_length/gold_length if gold_length > 0 else 0.0
        denom = (precision+recall)
        f1 = 2*precision*recall/denom if denom > 0 else 0.0
        return {
                "precision": precision,
                "recall": recall,
                "f1": f1
            }