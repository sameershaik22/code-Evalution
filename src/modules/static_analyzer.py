import ast

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

        results = {
            "syntax_valid": None,
            "errors": [],
            "constructs_found": [],
            "metrics": {},
            "style_issues": [],
            "conceptual_warnings": []
        }

        # ✅ Handle non-Python languages cleanly
        if language != 'python':
            results['syntax_valid'] = True
            results['constructs_found'].append(
                f"No static analysis performed for {language.upper()} code (Python-only feature)."
            )
            submission['analysis']['static'] = results
            print(f"[STATIC] Skipped static analysis for {student_id}: {language}")
            return submission

        # ✅ Python static analysis
        try:
            tree = ast.parse(code)
            results['syntax_valid'] = True

            # Metrics
            results['metrics']['for_loops'] = self._count_nodes(tree, ast.For)
            results['metrics']['while_loops'] = self._count_nodes(tree, ast.While)
            results['metrics']['if_statements'] = self._count_nodes(tree, ast.If)
            results['metrics']['function_definitions'] = self._count_nodes(tree, ast.FunctionDef)

            # Functions
            defined_funcs = self._find_function_defs(tree)
            results['constructs_found'].append(
                f"Defined functions: {', '.join(defined_funcs) if defined_funcs else 'None'}"
            )

            # Execution mode handling
            exec_mode = config.get('execution_mode', {})
            if isinstance(exec_mode, str):
                exec_mode = {"type": exec_mode}

            if exec_mode.get('type') == 'function':
                entry_point = exec_mode.get('entry_point')
                if entry_point and entry_point not in defined_funcs:
                    results['errors'].append(f"Expected function '{entry_point}' not defined.")
                    results['conceptual_warnings'].append(
                        f"You were expected to define a function named '{entry_point}', but it was not found."
                    )

            # Detect input usage
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id == 'input':
                        results['constructs_found'].append("Uses input()")
                        results['style_issues'].append(
                            "Consider handling invalid input using try-except for better robustness."
                        )
                        break

        except SyntaxError as e:
            results['syntax_valid'] = False
            results['errors'].append(
                f"Syntax Error: {e.msg} at line {e.lineno}, position {e.offset}"
            )
            results['constructs_found'] = ["Syntax error prevented further analysis"]

        submission['analysis']['static'] = results

        print(
            f"[STATIC] Analysis for {student_id}: "
            f"For loops: {results['metrics'].get('for_loops', 0)}, "
            f"Functions: {results['metrics'].get('function_definitions', 0)}"
        )

        return submission