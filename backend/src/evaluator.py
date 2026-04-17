import json
import re

class TokenEvaluator:

    @staticmethod
    def token_parsed_text(parsed_text: str) -> set[str]:
        tokens = parsed_text.split(" ")
        parsed_tokens = set()
        for token in tokens:
            parsed_tokens.add(token)

    @staticmethod
    def token_gold_text(gold_text: str) -> set[str]:
        tokens = gold_text.split(" ")
        parsed_tokens = set()
        for token in tokens:
            parsed_tokens.add(token)

    