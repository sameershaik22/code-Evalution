import docker
from pathlib import Path
import json

LANGUAGE_CONFIG = {
    "python": {
        "image": "python:3.10-slim",
        "run": "python3 {file}"
    },
    "cpp": {
        "image": "gcc:latest",
        "compile": "g++ {file} -o output",
        "run": "./output"
    },
    "c": {
        "image": "gcc:latest",
        "compile": "gcc {file} -o output",
        "run": "./output"
    },
    "java": {
        "image": "openjdk:17",
        "compile": "javac {file}",
        "run": "java {classname}"
    },
    "javascript": {
        "image": "node:18",
        "run": "node {file}"
    }
}

CONTAINER_WORKING_DIR = '/usr/src/app'
TIMEOUT = 5


class DynamicAnalyzer:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            print("[DYNAMIC] Docker client initialized.")
        except Exception as e:
            self.client = None
            print(f"[DYNAMIC] Docker init error: {e}")

    def run_code(self, code_path: Path, language: str, input_data: str):
        config = LANGUAGE_CONFIG.get(language)

        if not config:
            return None, "", f"Unsupported language: {language}"

        image = config["image"]
        filename = code_path.name

        try:
            # Build command
            if "compile" in config:
                compile_cmd = config["compile"].format(file=filename)

                if language == "java":
                    classname = filename.replace(".java", "")
                    run_cmd = config["run"].format(classname=classname)
                else:
                    run_cmd = config["run"]

                command = f"{compile_cmd} && echo '{input_data}' | {run_cmd}"
            else:
                command = f"echo '{input_data}' | {config['run'].format(file=filename)}"

            container = self.client.containers.run(
                image,
                command=f"/bin/sh -c \"{command}\"",
                volumes={
                    str(code_path.parent.resolve()): {
                        'bind': CONTAINER_WORKING_DIR,
                        'mode': 'rw'
                    }
                },
                working_dir=CONTAINER_WORKING_DIR,
                detach=True,
                stdout=True,
                stderr=True
            )

            # wait with timeout
            result = container.wait(timeout=TIMEOUT)
            exit_code = result["StatusCode"]

            logs = container.logs(stdout=True, stderr=True).decode()

            container.remove(force=True)

            return exit_code, logs.strip(), ""

        except Exception as e:
            return None, "", str(e)

    def analyze(self, submission: dict) -> dict:
        student_id = submission.get("student_id")
        print(f"\n[🔍] Analyzing submission for: {student_id}")

        if not self.client:
            submission['analysis']['dynamic'] = [{
                "name": "all_tests",
                "status": "skipped",
                "error": "Docker unavailable"
            }]
            return submission

        code_path = Path(submission['code_path'])
        config = submission['config']
        language = str(config.get('language', 'python')).lower()

        results = []

        for test in config.get("test_cases", []):
            name = test.get("name", "test")
            input_data = str(test.get("input", ""))
            expected = str(test.get("expected_output", "")).strip()

            print(f"\n[TEST] Running '{name}'...")

            exit_code, stdout, stderr = self.run_code(code_path, language, input_data)

            if exit_code is None:
                print(f"[RESULT] {name} → 🚨 ERROR")
                results.append({"name": name, "status": "system_error", "error": stderr})

            elif exit_code != 0:
                print(f"[RESULT] {name} → 💥 RUNTIME ERROR")
                results.append({"name": name, "status": "runtime_error", "error": stdout})

            elif stdout.strip() == expected:
                print(f"[RESULT] {name} → ✅ PASS")
                results.append({"name": name, "status": "pass"})

            else:
                print(f"[RESULT] {name} → ❌ FAIL")
                results.append({
                    "name": name,
                    "status": "fail",
                    "expected": expected,
                    "actual": stdout
                })

        submission['analysis']['dynamic'] = results
        print(f"\n[✅] Completed analysis for {student_id}")
        return submission