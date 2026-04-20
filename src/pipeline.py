import time
from pathlib import Path
from .modules.ingestion import Ingestor
from .modules.static_analyzer import StaticAnalyzer
from .modules.dynamic_analyzer import DynamicAnalyzer
from .modules.embedding_engine import EmbeddingEngine
from .modules.feedback_engine import FeedbackEngine
from .modules.feedback_generator import FeedbackGenerator
from .modules.analytics_engine import AnalyticsEngine


class Pipeline:
    def __init__(self, config_path_str: str, submissions_path_str: str,
                 output_path_str: str, execution_level: str = 'full'):
        """
        Initializes the Autograder pipeline with paths, modules, and execution level.
        """
        print("[PIPELINE] Initializing Autograder Pipeline...")
        
        self.config_path = Path(config_path_str)
        self.submissions_path = Path(submissions_path_str)
        self.output_path = Path(output_path_str)
        self.execution_level = execution_level.lower()

        # Base modules
        self.ingestor = Ingestor()
        self.static_analyzer = StaticAnalyzer()
        
        # Conditional modules
        self.dynamic_analyzer = DynamicAnalyzer() if self.execution_level in ["dynamic", "embedding", "full"] else None
        self.embedding_engine = EmbeddingEngine() if self.execution_level in ["embedding", "full"] else None
        self.feedback_engine = FeedbackEngine() if self.execution_level == "full" else None
        
        self.feedback_generator = FeedbackGenerator()
        self.analytics_engine = AnalyticsEngine()
        
        print(f"[PIPELINE] All necessary modules for level '{self.execution_level}' initialized.")

    def _get_assignment_id_from_submissions(self, submissions_data: list) -> str:
        if submissions_data and submissions_data[0].get('config'):
            return submissions_data[0]['config'].get('assignment_id', 'unknown_assignment')
        return "unknown_assignment"

    def _process_single_submission(self, submission_data: dict) -> dict:
        """
        Processes a single student submission through the configured analysis stages.
        """
        student_id = submission_data.get('student_id', 'UnknownStudent')
        print(f"\n--- Processing Submission for: {student_id} ---")

        if 'analysis' not in submission_data:
            submission_data['analysis'] = {}

        # ================= STAGE 1: STATIC =================
        analyzed_submission = self.static_analyzer.analyze(submission_data)

        # ================= STAGE 2: DYNAMIC =================
        if self.dynamic_analyzer:
            analyzed_submission = self.dynamic_analyzer.analyze(analyzed_submission)

        # ================= ✅ FINAL SCORE =================
        try:
            dynamic_results = analyzed_submission.get('analysis', {}).get('dynamic', [])

            passed = sum(1 for t in dynamic_results if t.get("status") == "pass")
            total = len(dynamic_results)

            test_score = passed / total if total > 0 else 0

            static_data = analyzed_submission.get('analysis', {}).get('static', {})
            similarity = static_data.get('similarity_score', 0)

            final_score = (0.5 * test_score + similarity) * 100

            analyzed_submission['analysis']['final_score'] = round(final_score, 2)

            print(f"[FINAL SCORE] {student_id}: {analyzed_submission['analysis']['final_score']}")

        except Exception as e:
            print("[FINAL SCORE ERROR]", e)

        # ================= STAGE 3: EMBEDDING =================
        if self.embedding_engine:
            analyzed_submission = self.embedding_engine.analyze(analyzed_submission)

        # ================= STAGE 4: FEEDBACK =================
        if self.feedback_engine:
            analyzed_submission = self.feedback_engine.analyze(analyzed_submission)

        print(f"--- Finished Processing for: {student_id} ---")
        return analyzed_submission

    def run(self):
        """
        Executes the full grading pipeline based on the configured level.
        """
        start_time = time.time()
        print("\n[PIPELINE] Starting grading process...")

        # 1. Ingestion
        raw_submissions_data = self.ingestor.load_submissions(
            str(self.config_path), str(self.submissions_path)
        )

        if not raw_submissions_data:
            print("[PIPELINE] No submissions found or loaded. Exiting.")
            return

        print(f"[PIPELINE] Ingested {len(raw_submissions_data)} submissions.")

        # 2. Processing
        processed_submissions = []

        for submission_data_item in raw_submissions_data:
            try:
                processed_submission = self._process_single_submission(submission_data_item)
                processed_submissions.append(processed_submission)
            except Exception as e:
                student_id = submission_data_item.get('student_id', 'UnknownStudent')
                print(f"[PIPELINE] ERROR processing {student_id}: {e}")

                processed_submissions.append({
                    "student_id": student_id,
                    "error_processing": str(e),
                    "config": submission_data_item.get('config', {}),
                    "analysis": {}
                })

        assignment_id_for_report = self._get_assignment_id_from_submissions(processed_submissions)

        # 3. Feedback Report
        if processed_submissions:
            self.feedback_generator.generate_all_reports(
                processed_submissions,
                str(self.output_path),
                assignment_id_for_report
            )
        else:
            print("[PIPELINE] No submissions processed.")

        # 4. Analytics
        print("\n[PIPELINE] Generating instructor analytics...")

        if processed_submissions and self.execution_level in ["embedding", "full"]:
            self.analytics_engine.generate_report(
                processed_submissions,
                str(self.output_path),
                assignment_id_for_report
            )
        else:
            print("[PIPELINE] Skipping analytics generation.")

        # 5. Completion
        end_time = time.time()
        total_time = end_time - start_time

        print(f"\n[PIPELINE] Completed in {total_time:.2f} seconds.")
        print(f"Reports available at: {self.output_path}")
           