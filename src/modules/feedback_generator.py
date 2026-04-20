from pathlib import Path
import csv


class FeedbackGenerator:

    def generate_individual_report_string(self, submission: dict) -> tuple:

        student_id = submission['student_id']
        full_code = submission.get('code', 'No code available.')

        # --- Dynamic Analysis ---
        dynamic_results = submission['analysis'].get('dynamic', [])
        total_tests = len(dynamic_results)
        passed_count = sum(1 for r in dynamic_results if r.get('status') == 'pass')

        # --- Feedback Engine ---
        feedback_results = submission['analysis'].get('feedback', {})
        technical_summary = feedback_results.get('technical_summary')
        debugging_insight = feedback_results.get('debugging_insight')
        custom_question_response = feedback_results.get('custom_question_response')
        analyzed_construct = feedback_results.get('analyzed_construct')

        report_lines = []
        report_lines.append(f"\n\n--- Feedback Report for: {student_id} ---")
        report_lines.append(f"Assignment: {submission['config']['assignment_id']}")

        # ================= STATIC =================
        report_lines.append("\n--- STATIC ANALYSIS (Code Structure & Potential Issues) ---\n")

        static_results = submission['analysis'].get('static', {})

        if not static_results.get('syntax_valid', False):
            report_lines.append("Your code has one or more Syntax Errors.")
            for err in static_results.get('errors', []):
                report_lines.append(f"- {err}")
        else:
            report_lines.append("Your code has valid syntax.")
            metrics = static_results.get('metrics', {})
            report_lines.append(f"- For Loops: {metrics.get('for_loops', 0)}")
            report_lines.append(f"- Function Definitions: {metrics.get('function_definitions', 0)}")

        # ================= CODE QUALITY =================
        report_lines.append("\n--- CODE QUALITY SCORES ---\n")

        def safe(val):
            return f"{val:.2f}" if isinstance(val, (int, float)) else "0.00"

        report_lines.append(f"- Lexical Score: {safe(static_results.get('lexical_score'))}")
        report_lines.append(f"- CodeBLEU Score: {safe(static_results.get('code_bleu_score'))}")
        report_lines.append(f"- AST Score: {safe(static_results.get('ast_score'))}%")

        # ================= FINAL SCORE (ADDED) =================
        final_score = submission.get("analysis", {}).get("final_score", "N/A")

        report_lines.append("\n--- FINAL SCORE ---\n")
        report_lines.append(f"Overall Score: {final_score} / 100\n")

        # ================= DYNAMIC =================
        report_lines.append("\n--- DYNAMIC ANALYSIS (Test Results) ---\n")

        if not dynamic_results:
            report_lines.append("No dynamic test results available.")
        else:
            for result in dynamic_results:
                status = result.get('status', 'ERROR').upper()

                report_lines.append(f"- Test Case {result.get('test_case', 'N/A')}: {status}")

                report_lines.append(f"  - Input: `{result.get('input', '')}`")
                report_lines.append(f"  - Expected: `{result.get('expected_output', '')}`")
                report_lines.append(f"  - Output: `{result.get('actual_output', '')}`")

                if status in ['FAIL', 'RUNTIME_ERROR', 'SYSTEM_ERROR']:
                    error_log = result.get('error', '')
                    if error_log:
                        report_lines.append(f"  - Error:\n```\n{error_log}\n```")

            report_lines.append(f"\n**Overall Score: {passed_count} / {total_tests} tests passed.**")

        # ================= AI FEEDBACK =================
        report_lines.append("\n--- AI-Generated Feedback ---\n")

        if technical_summary:
            report_lines.append(f"Technical Summary:")
            report_lines.append(f"```\n{technical_summary}\n```")
        else:
            report_lines.append("- Technical summary was not generated.")

        if debugging_insight:
            report_lines.append("\nDebugging Insight:")
            report_lines.append(f"```\n{debugging_insight}\n```")

        if custom_question_response:
            report_lines.append("\nResponse to Instructor's Question:")
            report_lines.append(f"```\n{custom_question_response}\n```")

        return (
            "\n".join(report_lines),
            student_id,
            passed_count,
            total_tests,
            technical_summary,
            full_code
        )

    # ================= AGGREGATED REPORT =================
    def generate_aggregated_report(self, all_submissions: list, output_dir_str: str, assignment_id: str):

        print(f"✔️ [FEEDBACK] Generating aggregated markdown report...")
        output_dir = Path(output_dir_str)
        output_dir.mkdir(parents=True, exist_ok=True)

        report_filename = f"Report_{assignment_id.replace(' ', '_')}.md"
        output_filepath = output_dir / report_filename

        full_report_content = [
            f"# Autograder - Aggregated Feedback Report",
            f"## Assignment: {assignment_id}\n"
        ]

        if not all_submissions:
            full_report_content.append("No submissions were processed.")
        else:
            for submission in all_submissions:
                individual_report_str, _, _, _, _, _ = self.generate_individual_report_string(submission)
                full_report_content.append(individual_report_str)
                full_report_content.append("\n" + "=" * 80 + "\n")

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(full_report_content))

        print(f"   => Aggregated markdown report saved to {output_filepath}")

    # ================= CSV =================
    def generate_csv_summary(self, all_submissions: list, output_dir_str: str, assignment_id: str):

        print(f"✔️ [FEEDBACK] Generating CSV summary...")
        output_dir = Path(output_dir_str)
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_filename = f"Summary_{assignment_id.replace(' ', '_')}.csv"
        output_filepath = output_dir / csv_filename

        headers = [
            'student_id',
            'tests_passed',
            'tests_total',
            'score_percentage',
            'final_score',   # ⭐ ADDED
            'semantic_summary',
            'code_snippet'
        ]

        processed_data_for_csv = []

        if not all_submissions:
            print("   => No data to write to CSV.")
            return

        for submission in all_submissions:
            try:
                _, student_id, passed_count, total_tests, summary, code_snippet = \
                    self.generate_individual_report_string(submission)

                score_percentage = (passed_count / total_tests * 100) if total_tests > 0 else 0
                final_score = submission.get("analysis", {}).get("final_score", "N/A")

                summary_for_csv = summary.replace('\n', ' ') if summary else "N/A"
                code_for_csv = code_snippet.replace('\n', '\\n') if code_snippet else "No Code Found"

                processed_data_for_csv.append({
                    'student_id': student_id,
                    'tests_passed': passed_count,
                    'tests_total': total_tests,
                    'score_percentage': f"{score_percentage:.2f}",
                    'final_score': final_score,
                    'semantic_summary': summary_for_csv,
                    'code_snippet': code_for_csv
                })

            except Exception as e:
                student_id = submission.get('student_id', 'UnknownStudent')
                print(f"   [WARNING] CSV error for {student_id}: {e}")

        try:
            with open(output_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(processed_data_for_csv)

            print(f"   => CSV summary saved to {output_filepath}")

        except Exception as e:
            print(f"   [ERROR] Failed to write CSV: {e}")

    # ================= MASTER =================
    def generate_all_reports(self, all_submissions: list, output_dir_str: str, assignment_id: str):

        if not all_submissions:
            print("[FEEDBACK] No submissions provided.")
            return

        self.generate_aggregated_report(all_submissions, output_dir_str, assignment_id)
        self.generate_csv_summary(all_submissions, output_dir_str, assignment_id)