import torch
from transformers import AutoTokenizer, AutoModel, RobertaTokenizer, AutoModelForCausalLM
import ast
import numpy as np
import astor
from .embedding_engine import EmbeddingEngine
from .prompt_pool import PROMPT_POOL
from sklearn.metrics.pairwise import cosine_similarity
from langchain_ollama import ChatOllama

OLLAMA_MODEL_ID = "mistral"


def ollama_generate(model_tag: str, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    print(f"  [OLLAMA_CLIENT] Calling model '{model_tag}' via Ollama...")
    try:
        llm = ChatOllama(
            model=model_tag,
            temperature=temperature,
            repetition_penalty=1.3,
            request_timeout=60,
            thinking=False,
        )
        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]

        import re
        raw_output = llm.invoke(messages).content
        ai_msg_content = re.sub(r"<thinking>.*?</thinking>", "", raw_output, flags=re.DOTALL)

        print(f"  [OLLAMA_CLIENT] Received response from Ollama.")
        return ai_msg_content

    except Exception as e:
        print(f"[OLLAMA_CLIENT] ERROR: {e}")
        return f"Error: Could not get response from Ollama model {model_tag}."


class FeedbackEngine:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[SEMANTIC_ENGINE] Running on {self.device}")

        self.embedding_engine = EmbeddingEngine()
        self.prompt_pool_data = []
        self._initialize_prompt_pool()

    def _initialize_prompt_pool(self):
        if not self.embedding_engine or not self.embedding_engine.model:
            print("[FEEDBACK_ENGINE] Embedding disabled")
            return

        for prompt_item in PROMPT_POOL:
            try:
                embedding = self.embedding_engine.get_code_embedding(prompt_item["text"])
                if embedding:
                    self.prompt_pool_data.append({
                        "id": prompt_item["id"],
                        "text": prompt_item["text"],
                        "embedding": np.array(embedding)
                    })
            except:
                pass

    def _find_best_prompt(self, target_embedding):
        if not self.prompt_pool_data or target_embedding is None:
            return ""

        try:
            target_vector = np.array(target_embedding).reshape(1, -1)
            prompt_vectors = np.array([item["embedding"] for item in self.prompt_pool_data])

            similarities = cosine_similarity(target_vector, prompt_vectors)
            idx = np.argmax(similarities)

            return self.prompt_pool_data[idx]["text"]
        except:
            return ""

    
    def get_technical_summary(self, code_snippet: str, error_message: str, language: str, question: str):

        system_prompt = f"""
You are a friendly and experienced programming mentor.

You are reviewing {language.upper()} code.

Talk like a real human mentor — not like a machine or formal report.

Tone:
- supportive and encouraging
- slightly informal (like talking to a student)
- clear and easy to understand
- practical and honest

Speak directly to the student using "you".

Use natural phrases like:
- "Nice attempt 👏"
- "Good job 👍"
- "Your code is working, but..."
- "You're on the right track"
- "Here’s where you can improve"
- "Try doing it this way instead"

Avoid robotic or textbook-style language.

---

Language-specific guidance:
- C / C++ → mention performance, memory, pointers, efficiency
- Java → mention OOP, structure, Scanner/BufferedReader usage
- Python → mention readability, simplicity, Pythonic style
- JavaScript → mention async, functions, clean structure
- C# → mention types and .NET practices
- Go → mention simplicity and concurrency
- TypeScript → mention type safety

---

Structure your response like this:

Explanation:
Explain what the code is doing in simple, friendly language.

Correctness:
Tell if it works or not in a natural way (like a mentor talking).

Issues:
Mention mistakes clearly (don’t be harsh).

Improvements:
Explain how to fix them in a practical way.

Review:
Give an overall opinion like you're talking to the student.

Learning:
Tell what concept the student should focus on next.

Practice:
- Suggest 2–3 small practice ideas

---

Important:
- Keep it human and conversational
- Avoid long paragraphs
- Don’t sound like a report
- Make it feel like real feedback from a mentor

"""

        error_text = error_message if error_message else "No runtime errors"

        best_prompt = ""
        if self.embedding_engine:
            emb = self.embedding_engine.get_code_embedding(code_snippet)
            if emb:
                best_prompt = self._find_best_prompt(emb)

        user_prompt = f"""
Problem:
{question}

Language:
{language}

Code:
{code_snippet}

Errors:
{error_text}

Hint:
{best_prompt}

Give full feedback.
"""

        response = ollama_generate(OLLAMA_MODEL_ID, system_prompt, user_prompt)

        if not response or "Error" in response:
            return "AI feedback could not be generated. Please check Ollama setup."

        return response.strip()

    def analyze(self, submission: dict):

        student_id = submission['student_id']
        config = submission['config']
        code = submission.get('code', '')

        language = submission.get('config', {}).get('language', 'python')
        language = language.lower()
        question = config.get('question', '')

        print(f"[FEEDBACK_ENGINE] Processing {student_id}")

        if 'feedback' not in submission['analysis']:
            submission['analysis']['feedback'] = {}

        dynamic_results = submission['analysis'].get('dynamic', [])

        errors = []
        for t in dynamic_results:
            if t.get("status") == "runtime_error":
                errors.append(t.get("error", ""))

        error_message = "\n".join(errors)

        summary = self.get_technical_summary(code, error_message, language, question)

        submission['analysis']['feedback']['technical_summary'] = summary

        return submission