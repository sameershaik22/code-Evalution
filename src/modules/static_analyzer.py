import ast

# ✅ IMPORTS
from .evaluation_engine.core_similarity.lexical_scorer import LexicalScorer
from .evaluation_engine.core_similarity.codebleu_legacy import CodeBLEU
from .evaluation_engine.core_similarity.weighted_ngram_scorer import WeightedNGramScorer

# ✅ SAFE AST IMPORT
try:
    from .evaluation_engine.core_similarity.ast.ast_similarity import compute_ast_similarity
except:
    compute_ast_similarity = None


class StaticAnalyzer:

    def _count_nodes(self, tree, node_type):
        return sum(1 for node in ast.walk(tree) if isinstance(node, node_type))

    def _find_function_defs(self, tree):
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    def analyze(self, submission: dict) -> dict:
        student_id = submission['student_id']
        print(f"[STATIC] Analyzing code for {student_id}...")

        code = submission['code']
        config = submission['config']
        language = str(config.get('language', 'python')).lower()

        # 🔥 Normalize language names
        if language == "js":
            language = "javascript"
        if language == "c++":
            language = "cpp"

        # 🔥 Reference code
        reference_solutions = config.get("reference_solutions", {})
        reference_code = reference_solutions.get(language, "")

        # 🔥 INIT SCORERS
        lex_scorer = LexicalScorer()
        codebleu = CodeBLEU()
        ngram_scorer = WeightedNGramScorer()

        results = {
            "syntax_valid": None,
            "errors": [],
            "constructs_found": [],
            "metrics": {},
            "style_issues": [],
            "conceptual_warnings": [],
            "lexical_score": 0.0,
            "weighted_ngram_score": 0.0,
            "weight_2gram_score": 0.0,
            "weight_3gram_score": 0.0,
            "code_bleu_score": 0.0,
            "ast_score": 0.0,
            "similarity_score": 0.0   # ⭐ NEW
        }

        # ================= NON-PYTHON =================
        if language != 'python':
            results['syntax_valid'] = True
            results['constructs_found'].append(
                f"No static analysis performed for {language.upper()} code."
            )

            if reference_code:
                try:
                    # ✅ FIXED LEXICAL
                    lex_result = lex_scorer.score(reference_code, code)

                    # ✅ FIXED NGRAM
                    weign_result = ngram_scorer.score(reference_code, code, language=language)
                    weign_result_2 = ngram_scorer.score(reference_code, code, language=language, n=2)
                    weign_result_3 = ngram_scorer.score(reference_code, code, language=language, n=3)

                    # CODEBLEU
                    bleu_result = codebleu.score(reference_code, code, language)

                    if isinstance(bleu_result, dict):
                        codebl_result = float(bleu_result.get("code_bleu", 0))
                    elif hasattr(bleu_result, "score"):
                        codebl_result = float(bleu_result.score)
                    else:
                        try:
                            codebl_result = float(bleu_result)
                        except:
                            codebl_result = 0.0

                    # ✅ FIXED AST (WITH FALLBACK)
                    try:
                        if compute_ast_similarity:
                            ast_score = float(compute_ast_similarity(reference_code, code))
                        else:
                            tree1 = ast.parse(reference_code)
                            tree2 = ast.parse(code)
                            ast_score = 1.0 if ast.dump(tree1) == ast.dump(tree2) else 0.5
                    except:
                        ast_score = 0.0

                    # ✅ NORMALIZE + FINAL SCORE
                    lex = min(max(float(lex_result), 0), 1)
                    bleu = min(max(float(codebl_result), 0), 1)
                    ast_val = min(max(float(ast_score), 0), 1)

                    similarity = (0.1 * lex) + (0.2 * bleu) + (0.2 * ast_val)

                    results.update({
                        'lexical_score': round(lex, 3),
                        'weighted_ngram_score': float(weign_result),
                        "weight_2gram_score": float(weign_result_2),
                        "weight_3gram_score": float(weign_result_3),
                        "code_bleu_score": round(bleu, 3),
                        'ast_score': round(ast_val, 3),
                        'similarity_score': round(similarity, 3)
                    })

                except Exception as e:
                    print("[STATIC ERROR NON-PYTHON]", e)

            submission['analysis']['static'] = results
            return submission

        # ================= PYTHON STATIC =================
        try:
            tree = ast.parse(code)
            results['syntax_valid'] = True

            results['metrics']['for_loops'] = self._count_nodes(tree, ast.For)
            results['metrics']['while_loops'] = self._count_nodes(tree, ast.While)
            results['metrics']['if_statements'] = self._count_nodes(tree, ast.If)
            results['metrics']['function_definitions'] = self._count_nodes(tree, ast.FunctionDef)

            defined_funcs = self._find_function_defs(tree)
            results['constructs_found'].append(
                f"Defined functions: {', '.join(defined_funcs) if defined_funcs else 'None'}"
            )

            if reference_code:
                try:
                    # LEXICAL
                    lex_result = lex_scorer.score(reference_code, code)

                    # NGRAM
                    weign_result = ngram_scorer.score(reference_code, code, language=language)
                    weign_result_2 = ngram_scorer.score(reference_code, code, language=language, n=2)
                    weign_result_3 = ngram_scorer.score(reference_code, code, language=language, n=3)

                    # CODEBLEU
                    bleu_result = codebleu.score(reference_code, code, language)

                    if isinstance(bleu_result, dict):
                        codebl_result = float(bleu_result.get("code_bleu", 0))
                    elif hasattr(bleu_result, "score"):
                        codebl_result = float(bleu_result.score)
                    else:
                        try:
                            codebl_result = float(bleu_result)
                        except:
                            codebl_result = 0.0

                    # ✅ FIXED AST
                    try:
                        if compute_ast_similarity:
                            ast_score = float(compute_ast_similarity(reference_code, code))
                        else:
                            tree1 = ast.parse(reference_code)
                            tree2 = ast.parse(code)
                            ast_score = 1.0 if ast.dump(tree1) == ast.dump(tree2) else 0.5
                    except Exception as e:
                        print("[AST ERROR]", e)
                        ast_score = 0.0

                    # ✅ NORMALIZE + FINAL SCORE
                    lex = min(max(float(lex_result.score), 0), 1)
                    bleu = min(max(float(codebl_result), 0), 1)
                    ast_val = min(max(float(ast_score), 0), 1)

                    similarity = (0.1 * lex) + (0.2 * bleu) + (0.2 * ast_val)

                    results.update({
                        'lexical_score': round(lex, 3),
                        'weighted_ngram_score': weign_result,
                        "weight_2gram_score": weign_result_2,
                        "weight_3gram_score": weign_result_3,
                        "code_bleu_score": round(bleu, 3),
                        'ast_score': round(ast_val, 3),
                        'similarity_score': round(similarity, 3)
                    })

                except Exception as e:
                    print("[STATIC ERROR PYTHON]", e)

        except SyntaxError as e:
            results['syntax_valid'] = False
            results['errors'].append(str(e))

        submission['analysis']['static'] = results
        return submission