from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple
from app.services.evaluation_engine.core_similarity.lexical_scorer import LexicalScorer

Language = Literal['python', 'c++', 'c', 'java', 'javascript']

LANGUAGE_TOKEN_WEIGHTS: Dict[Language, Dict[str, float]] = {
    "python": {
        "def": 2.0,
        "return": 2.0,
        "for": 1.8,
        "while": 1.8,
        "if": 1.6,
        "elif": 1.6,
        "else": 1.6,
        "import": 1.5,
        "from": 1.5,
    },
    "c": {
        "int": 1.8,
        "float": 1.8,
        "return": 2.0,
        "for": 1.8,
        "while": 1.8,
        "if": 1.6,
    },
    "c++": {
        "int": 1.8,
        "float": 1.8,
        "return": 2.0,
        "for": 1.8,
        "while": 1.8,
        "if": 1.6,
        "std": 1.5,
        "cout": 1.4,
    },
    "java": {
        "class": 2.0,
        "public": 1.5,
        "static": 1.5,
        "void": 1.5,
        "return": 2.0,
        "for": 1.8,
        "while": 1.8,
        "if": 1.6,
        "new": 1.4,
    },
    "javascript": {
        "function": 2.0,
        "return": 2.0,
        "for": 1.8,
        "while": 1.8,
        "if": 1.6,
        "let": 1.4,
        "const": 1.4,
        "var": 1.4,
    },
}


@dataclass(frozen=True)
class WeightedNGramScoreFormat :
    score : float
    n : int  #Nth gram
    un : float
    inter : float
    common_grams : Dict[Tuple[str, str, ...], float]
    explanation : str

class WeightedNGramScorer:

    def score(self, candidate_tokens : List[str], reference_tokens : List[str], language:Language , n:int = 3) -> WeightedNGramScoreFormat:
        
        candidate_ngrams = self._ngram_generation(candidate_tokens, n)
        reference_ngrams = self._ngram_generation(reference_tokens, n)

        candidate_counter = Counter(candidate_ngrams)
        reference_counter = Counter(reference_ngrams)

        intersection_weight , shared_ngrams = self._weighted_intersection(candidate_counter , reference_counter, language)

        candidate_weights = self._weighted_score(candidate_counter, language) # Weighted frequency of each gram in candidate grams.
        reference_weights = self._weighted_score(reference_counter, language) # Same as above but for reference grams.
        union_weight = (candidate_weights + reference_weights - intersection_weight) #Need to consider this and calculate accordingly, and yes we did change it.

        score = 1.0 if union_weight == 0 else intersection_weight/union_weight
        explanation = self._explain(score, n, shared_ngrams, language)
        return WeightedNGramScoreFormat(
            score=score,
            n=n,
            un = union_weight,
            inter = intersection_weight,
            common_grams = shared_ngrams,
            explanation=explanation,
        )

    @staticmethod
    def _ngram_generation(tokens : List[str] , n:int) -> List[Tuple[str, ...]]:
        if len(tokens) < n:
            return []

        return [
            tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)
        ]

    @staticmethod
    def _weighted_intersection(candidate_counter : Counter, reference_counter:Counter , language:Language) -> Tuple[float, int]:
        weights = LANGUAGE_TOKEN_WEIGHTS.get(language, {})
        total_weight = 0.0
        shared_ngrams = 0

        for ngram in candidate_counter.keys() & reference_counter.keys():
            frequency = min(candidate_counter[ngram], reference_counter[ngram])
            weight = sum(weights.get(token,1.0) for token in ngram)

            total_weight += frequency*weight
            shared_ngrams += frequency
        return total_weight , shared_ngrams

    
    @staticmethod
    def _weighted_score(counter: Counter, language:Language) -> float:
        weights = LANGUAGE_TOKEN_WEIGHTS.get(language, {})
        weight_score = 0.0

        for ngram in counter.keys():
            weight = sum(weights.get(token, 1.0) for token in ngram)

            weight_score += counter[ngram]*weight
        return weight_score


    @staticmethod
    def _explain(score: float,n: int, shared: int, language: Language) -> str:

        if score > 0.75:
            level = "very high"
        elif score > 0.55:
            level = "high"
        elif score > 0.35:
            level = "moderate"
        elif score > 0.15:
            level = "low"
        else:
            level = "very low"

        return f"""
        Weighted {n}-gram similarity for {language} code is {level}.

        Score: {score:.3f}

        {shared} shared n-grams detected with language-aware weighting.
        """.strip()

