import json
from pathlib import Path

class Ingestor:
    def load_submissions(self, config_path: str, submissions_path: str) -> list:
        """
        Loads submissions from a specified directory.
        Handles two structures:
        1. Directory-based: submissions_path/student_id/code.py
        2. File-based:     submissions_path/student_id.py
        """
        print("[INGESTOR] Loading assignment config and submissions...")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                assignment_config = json.load(f)
        except FileNotFoundError:
            print(f"[INGESTOR] ERROR: Assignment config file not found at '{config_path}'")
            return []
        except json.JSONDecodeError:
            print(f"[INGESTOR] ERROR: Assignment config file at '{config_path}' is not valid JSON.")
            return []

        submissions = []
        root_path = Path(submissions_path)
        
        if not root_path.is_dir():
            print(f"[INGESTOR] ERROR: Submissions path '{submissions_path}' is not a valid directory.")
            return []

        supported_extensions = {
            '.py': 'python',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.cs': 'csharp',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.swift': 'swift'
        }

        print(f"[INGESTOR] Scanning for submissions in: {root_path}")
        for item_path in root_path.iterdir():
            submission_data = None
            language = None
            code_file_path = None

            # --- Case 1: Item is a directory with a supported code file ---
            if item_path.is_dir():
                student_id = item_path.name
                for ext, lang in supported_extensions.items():
                    files = list(item_path.glob(f'*{ext}'))
                    if files:
                        code_file_path = files[0]
                        language = lang
                        break

                if code_file_path is None:
                    print(f"  [INGESTOR] WARNING: No supported code file found in directory for student: {student_id}")
                else:
                    print(f"  [INGESTOR] Found directory submission for '{student_id}' at '{code_file_path}'")

            # --- Case 2: Item is a supported code file directly in the submissions folder ---
            elif item_path.is_file() and item_path.suffix.lower() in supported_extensions:
                student_id = item_path.stem
                code_file_path = item_path
                language = supported_extensions[item_path.suffix.lower()]
                print(f"  [INGESTOR] Found direct file submission for '{student_id}' at '{code_file_path}'")

            if code_file_path is not None:
                try:
                    with open(code_file_path, 'r', encoding='utf-8') as f:
                        code = f.read()

                    submission_config = dict(assignment_config)
                    file_language = language or submission_config.get('language', 'python')
                    submission_config['language'] = submission_config.get('language', file_language)

                    submission_data = {
                        "student_id": student_id,
                        "code_path": str(code_file_path),
                        "code": code,
                        "config": submission_config,
                        "analysis": {}
                    }
                except Exception as e:
                    print(f"  [INGESTOR] ERROR: Could not read file '{code_file_path}'. Details: {e}")

            if submission_data:
                submissions.append(submission_data)

        if not submissions:
             print(f"[INGESTOR] WARNING: No valid submissions found in '{submissions_path}'. Please check directory structure and file names.")
             
        return submissions
