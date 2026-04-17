import json
import re
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
    def evaluate(parsed_text: str, gold_text: str) -> Dict[str,Dict[int]]:
        pass