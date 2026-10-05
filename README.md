# ✦ Lumina

An AI study studio: photograph a problem or a page of handwritten notes, then get **hints**, **flashcards** and **quizzes**. Built on **Gemma 4**, Google's open-weights multimodal model, via the Gemini API, for Hacktoberfest 2026 Hack Day (Android Club VITC).

## Features
- **Tutor:** three hint levels (Nudge, Method, Full solution) plus follow-up chat
- **Study Lab:** notes to index-card flashcards, multiple-choice quizzes with explanations, Anki CSV export
- Home dashboard with progress saved in your browser
- English, Tamil and Hindi

## How it works
`index.html` is the whole frontend (plain HTML, CSS and JavaScript). `api/gemma.py` is a Vercel Python function that holds the prompts and calls Gemma 4, so the API key never reaches the browser.

## Deploy on Vercel
1. Push this repo to GitHub and import it in Vercel (framework preset: **Other**).
2. Add the environment variable `GEMINI_API_KEY` (free key: aistudio.google.com/apikey).
3. Deploy.

## Tech stack
1. Model: Gemma 4 (open weights) via the Gemini API
2. Frontend: plain HTML, CSS and JavaScript
3. Backend: Python serverless function on Vercel
4. License: MIT

## Roadmap
Local Gemma 4 via Ollama, spaced repetition, more languages.

## License
MIT
