from langchain_ollama import ChatOllama

OLLAMA_MODEL_ID = "mistral"


def ollama_generate(system_prompt: str, user_prompt: str, temperature: float = 0.5) -> str:
    print(f"  [OLLAMA_CLIENT] Calling model '{OLLAMA_MODEL_ID}' via Ollama...")
    try:
        llm = ChatOllama(
            model=OLLAMA_MODEL_ID,
            temperature=temperature,
            request_timeout=60,
        )

        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]

        response = llm.invoke(messages).content

        print(f"  [OLLAMA_CLIENT] Received response from Ollama.")
        return response

    except Exception as e:
        print(f"[OLLAMA_CLIENT] ERROR: {e}")
        return "AI feedback could not be generated. Please check Ollama setup."


class FeedbackEngine:

    def should_call_llm(self, dynamic_results):
        return True

    def get_system_prompt(self, language: str):
        return f"""
You are a friendly and experienced coding mentor.

Talk like a real human mentor — not like a report.

Tone:
- supportive
- encouraging
- slightly informal
- clear and practical

Talk directly to the student using "you".

Programming Language: {language.upper()}

Structure:

Start with something like:
"Nice attempt!" or "Good job getting this working!"

Explanation:
Explain what the code is doing simply.

Correctness:
Say if it works or not.

Issues:
Explain mistakes (if any).

Improvements:
Give practical suggestions.

Review:
Give overall mentor-style feedback.

Learning:
What the student should learn next.

Practice:
Give 2–3 small practice ideas.

IMPORTANT:
- Follow this structure EXACTLY
- Do not skip any section
- Use clear headings

Keep it natural and human-like.
"""

    def analyze(self, submission: dict):

        student_id = submission['student_id']
        print(f"[FEEDBACK_ENGINE] Processing {student_id}")

        if 'feedback' not in submission['analysis']:
            submission['analysis']['feedback'] = {}

        code = submission.get('code', '')
        language = submission.get('config', {}).get('language', 'python').lower()
        question = submission.get('config', {}).get('question', '')

        dynamic_results = submission['analysis'].get('dynamic', [])
        static_results = submission['analysis'].get('static', {})

        # ================= SCORES (ADDED) =================
        lexical = static_results.get("lexical_score", 0)
        codebleu = static_results.get("code_bleu_score", 0)
        ast_score = static_results.get("ast_score", 0)
        final_score = submission.get('analysis', {}).get('final_score', "N/A")

        # ================= ERRORS =================
        errors = []
        for t in dynamic_results:
            if t.get("status") in ["runtime_error", "system_error"]:
                errors.append(t.get("error", ""))

        error_message = "\n".join(errors) if errors else "No runtime errors"

        # ================= TEST RESULTS =================
        passed = sum(1 for t in dynamic_results if t.get("status") == "pass")
        failed = len(dynamic_results) - passed

        system_prompt = self.get_system_prompt(language)

        # ================= PROMPT (UPDATED WITH SCORES) =================
        user_prompt = f"""
Problem:
{question}

Code:
{code}

Test Results:
Passed: {passed}
Failed: {failed}

Code Quality Scores:
Lexical Score: {lexical}
CodeBLEU Score: {codebleu}
AST Score: {ast_score}

Final Score:
{final_score} / 100

Errors:
{error_message}

Give helpful feedback to the student.
"""

        print("⚡ Calling AI feedback...")

        response = ollama_generate(system_prompt, user_prompt)

        submission['analysis']['feedback']['technical_summary'] = response.strip()

        # ================= STORE SCORES (ADDED) =================
        submission['analysis']['feedback']['scores'] = {
            "lexical": lexical,
            "codebleu": codebleu,
            "ast": ast_score,
            "final": final_score
        }

        return submission