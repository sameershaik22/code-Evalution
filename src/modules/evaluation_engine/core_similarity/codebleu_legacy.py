from codebleu import calc_codebleu
from typing import Dict, Tuple
from functools import lru_cache
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeBLEUFormat:
    score: float
    ngram_match_score: float
    weighted_ngram_match_score: float
    syntax_match_score: float
    dataflow_match_score: float
    explanation: str


class CodeBLEU:

    def __init__(self, weights=(0.25, 0.25, 0.25, 0.25)):
        self.weights = weights

    @staticmethod
    @lru_cache(maxsize=500)
    def _cached_score(code: str, reference_code: str, language: str, weights: Tuple) -> Dict:
        result = calc_codebleu( predictions=[code], references=[[reference_code]],lang=language, weights=weights
        )
        return result

    def score(self, code: str, reference_code: str, language: str) -> CodeBLEUFormat:
        result = self._cached_score(code, reference_code, language, self.weights)

        explanation = self._explanation(result)

        return CodeBLEUFormat(
            score=result.get("codebleu", 0.0),
            ngram_match_score=result.get("ngram_match_score", 0.0),
            weighted_ngram_match_score=result.get("weighted_ngram_match_score", 0.0),
            syntax_match_score=result.get("syntax_match_score", 0.0),
            dataflow_match_score=result.get("dataflow_match_score", 0.0),
            explanation=explanation
        )

    @staticmethod
    def _explanation(result: Dict) -> str:
        score = result.get("codebleu", 0.0)

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
            f"Code similarity is {level} (CodeBLEU={score:.3f}).\n\n"
            f"- N-gram match: {result.get('ngram_match_score', 0.0):.3f}\n"
            f"- Weighted n-gram match: {result.get('weighted_ngram_match_score', 0.0):.3f}\n"
            f"- Syntax match: {result.get('syntax_match_score', 0.0):.3f}\n"
            f"- Dataflow match: {result.get('dataflow_match_score', 0.0):.3f}\n\n"
            f"This score captures lexical, syntactic, and semantic similarity of code."
        )

if __name__ == '__main__':
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

    javascript_code = """
    function reverseStringCandidate(str) {
    let reversed = "";
    for (let i = str.length - 1; i >= 0; i--) {
        reversed += str[i];
    }
    return reversed;
    }
    """
    javascript_ref_code = """
    function reverseStringReference(str) {
        return str.split('').reverse().join('');
    }

    """
    cb = CodeBLEU()
    result = cb.score(code = javascript_code , reference_code = javascript_ref_code, language = 'javascript')
    print(result)
