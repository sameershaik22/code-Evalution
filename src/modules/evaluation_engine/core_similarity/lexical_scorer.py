from __future__ import annotations
import re
from dataclasses import dataclass 
from collections import Counter
from typing import Dict, List


@dataclass(frozen=True) 
class LexicalScorerFormat:
    score: float
    common_tokens: Dict[str, int]
    candidate_token_count: int
    reference_token_count: int 
    explanation: str


class LexicalScorer:
    
    def score(self, candidate_code: str, reference_code: str) -> LexicalScorerFormat:
        # Tokenize raw code strings
        candidate_tokens = re.findall(r'\w+', candidate_code)
        reference_tokens = re.findall(r'\w+', reference_code)

        candidate_tokens__C = Counter(candidate_tokens)
        reference_tokens__C = Counter(reference_tokens)
        common_tokens_d = self._common_tokens(candidate_tokens__C, reference_tokens__C)

        lexical_score = self._compute_score(candidate_tokens__C, reference_tokens__C, common_tokens_d)

        explanation_s = self._explanation(lexical_score, candidate_tokens__C, reference_tokens__C, common_tokens_d)

        result = LexicalScorerFormat(
            score=lexical_score,
            common_tokens=common_tokens_d,
            candidate_token_count=sum(candidate_tokens__C.values()),
            reference_token_count=sum(reference_tokens__C.values()),
            explanation=explanation_s
        )
        return result  # ← only result, no tuple

    @staticmethod
    def _common_tokens(candidate_tokens: Counter, reference_tokens: Counter) -> Dict[str, int]:
        return {
            token: min(candidate_tokens[token], reference_tokens[token])
            for token in candidate_tokens.keys() & reference_tokens
        }

    @staticmethod
    def _compute_score(candidate_tokens: Counter, reference_tokens: Counter, common_tokens: Dict[str, int]) -> float:
        intersection = sum(common_tokens.values())
        union = int(sum(candidate_tokens.values()) + sum(reference_tokens.values()) - intersection)

        if union == 0:
            return 1.0
        
        return intersection / union

    @staticmethod
    def _explanation(score: float, candidate: Counter, reference: Counter, common_tokens: Dict[str, int]) -> str:
        if score > 0.8:
            level = "very high"
        elif score > 0.6:
            level = "high"
        elif score > 0.4:
            level = "moderate"
        elif score > 0.2:
            level = "low"
        else:
            level = "very low"

        return (
            f"Lexical similarity is {level} (score={score:.3f}). \n\n"
            f"The candidate and reference share "
            f"{len(common_tokens)} distinct tokens. \n\n"
            f"This score reflects surface-level similarity only \n\n"
            f"and does not consider syntax or semantics."
        )


if __name__ == "__main__":
    ls = LexicalScorer()
    code = """def compute_factorial(x):
    value = 1
    counter = 1

    while counter <= x:
        value = value * counter
        counter += 1
    
    return value

    number = 5
    print(compute_factorial(number))"""

    reference_code = """def factorial(n):
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result

    num = 5
    print(factorial(num))"""

    result = ls.score(code, reference_code)
    print(result)