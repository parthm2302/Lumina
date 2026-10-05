"""Lumina's backend: one Vercel function that calls Gemma 4 so the API key stays secret."""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

MODEL = "gemma-4-26b-a4b-it"  # alternative: "gemma-4-31b-it"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

LEVELS = {
    "Nudge": "Give ONE short nudge toward the key idea. No steps, no answer.",
    "Method": "Name the concept or formula and outline the approach in 2-4 bullets. Do NOT reveal the final answer.",
    "Full solution": "Walk through the full solution step by step and end with the final answer.",
}


def call(system, contents):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it in Vercel, then redeploy.")
    body = json.dumps({"systemInstruction": {"parts": [{"text": system}]}, "contents": contents}).encode()
    request = urllib.request.Request(URL, body, {"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(request, timeout=55) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Gemini API error {error.code}: {error.read().decode()[:200]}")
    parts = data["candidates"][0]["content"].get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


def json_list(text):
    a, b = text.find("["), text.rfind("]")
    if a == -1 or b < a:
        raise ValueError("The model did not return a list. Try again.")
    return json.loads(text[a : b + 1])


def images(items):
    return [{"inlineData": {"mimeType": i.get("mime", "image/jpeg"), "data": i["data"]}} for i in items[:4]]


def run(r):
    task, language = r.get("task"), str(r.get("language", "English"))[:20]
    pics = images(r.get("images", []))
    if not pics:
        raise ValueError("Please upload a photo first.")
    n = max(3, min(15, int(r.get("n", 8))))
    if task == "tutor":
        history = r.get("history", [])
        if not history or len(history) > 20:
            raise ValueError("Start a new problem to keep going.")
        contents = [
            {"role": "model" if m["role"] == "model" else "user",
             "parts": (pics if i == 0 else []) + [{"text": str(m["text"])[:2000]}]}
            for i, m in enumerate(history)
        ]
        system = (
            "You are Lumina, a patient tutor. The student shares a photo of a problem. "
            "First restate what it asks so they can confirm you read it right. "
            "Format with Markdown. Write all math in LaTeX: $...$ inline and $$...$$ for display equations. "
            f"Subject: {str(r.get('subject', 'General'))[:30]}. Reply in {language}. "
            f"Follow this hint level EXACTLY: {LEVELS.get(r.get('level'), LEVELS['Nudge'])}"
        )
        return {"text": call(system, contents)}
    if task == "cards":
        system = ("Read the study notes in the images. Use only what is written; skip unclear handwriting. "
                  'Reply with ONLY a JSON list: [{"question": "...", "answer": "..."}]')
        ask = f"Make {n} flashcards in {language}."
        items = json_list(call(system, [{"role": "user", "parts": pics + [{"text": ask}]}]))
        return {"items": [{"question": str(i["question"]).strip(), "answer": str(i["answer"]).strip()}
                          for i in items if isinstance(i, dict) and i.get("question") and i.get("answer")]}
    if task == "quiz":
        system = ("Read the study notes in the images. Use only what is written. Reply with ONLY a JSON list: "
                  '[{"question": "...", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "..."}] '
                  "where answer is the index (0-3) of the correct option.")
        ask = f"Write {n} multiple-choice questions in {language}."
        quiz = []
        for i in json_list(call(system, [{"role": "user", "parts": pics + [{"text": ask}]}])):
            try:
                options, answer = [str(o) for o in i["options"]], int(i["answer"])
                if len(options) == 4 and 0 <= answer < 4 and i["question"]:
                    quiz.append({"question": str(i["question"]), "options": options, "answer": answer,
                                 "explanation": str(i.get("explanation", ""))})
            except (KeyError, TypeError, ValueError):
                continue
        return {"items": quiz}
    raise ValueError("Unknown task.")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            code, out = 200, run(json.loads(self.rfile.read(size)))
        except Exception as error:
            code, out = 500, {"error": str(error)}
        body = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
