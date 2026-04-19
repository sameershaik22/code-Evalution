from typing import List, Dict
import difflib
from dataclasses import dataclass


@dataclass(frozen=True)
class ASTScoreFormat:
    score: float
    sequence_similarity: float
    jaccard_similarity: float
    candidate_node_count: int
    reference_node_count: int
    explanation: str


class ASTScore:

    def score(self, cand_nodes: List[str], ref_nodes: List[str]) -> ASTScoreFormat:
        sim_score = difflib.SequenceMatcher(None, cand_nodes, ref_nodes).ratio()
        set1, set2 = set(cand_nodes), set(ref_nodes)

        if len(set1 | set2) == 0:
            jaccard_score = 1.0
        else:
            jaccard_score = len(set1 & set2) / len(set1 | set2)

        final_score = 0.7 * sim_score + 0.3 * jaccard_score
        explanation = self._explanation(sim_score, jaccard_score, final_score)

        return ASTScoreFormat(
            score=final_score,
            sequence_similarity=sim_score,
            jaccard_similarity=jaccard_score,
            candidate_node_count=len(cand_nodes),
            reference_node_count=len(ref_nodes),
            explanation=explanation
        )

    @staticmethod
    def _explanation(seq: float, jac: float, final: float) -> str:
        if final > 0.8:
            level = "very high"
        elif final > 0.6:
            level = "high"
        elif final > 0.4:
            level = "moderate"
        elif final > 0.2:
            level = "low"
        else:
            level = "very low"

        return (
            f"AST structural similarity is {level} (score={final:.3f}).\n\n"
            f"- Sequence similarity (order-sensitive): {seq:.3f}\n"
            f"- Jaccard similarity (structure overlap): {jac:.3f}\n\n"
            f"Sequence similarity captures execution structure/order,\n"
            f"while Jaccard measures structural overlap of constructs."
        )


