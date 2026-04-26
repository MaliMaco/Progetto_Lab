from typing import Dict, Counter
from collections import Counter

class TokenEvaluator:

    @staticmethod
    def normalize(text: str) -> str:
        text = text.strip()
        return text

    @staticmethod
    def token_parsed_text(parsed_text: str) -> Counter[str]:
        cleaned_tokens = TokenEvaluator.normalize(parsed_text)
        tokens = cleaned_tokens.strip().split()
        parsed_tokens = Counter(tokens)
        return parsed_tokens

    @staticmethod
    def token_gold_text(gold_text: str) -> Counter[str]:
        cleaned_tokens = TokenEvaluator.normalize(gold_text)
        tokens = cleaned_tokens.strip().split()
        parsed_tokens = Counter(tokens)
        return parsed_tokens

    @staticmethod
    def evaluate(parsed_text: Counter[str], gold_text: Counter[str]) -> Dict[str,float]:
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