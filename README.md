# Math AI Tutor

Full-stack math evaluation and tutoring workspace with a Django REST backend, a React front end, and LangChain-powered LLM orchestration for OpenAI and Google Gemini models.

## Project Structure
```
Math_AI/
├── api/                 # Django app with LangChain services and prompts
├── edmaster_backend/    # Django project settings and URLs
├── frontend/            # React single-page application
├── manage.py            # Django management entry point
├── requirements.txt     # Python dependencies (backend)
└── README.md
```

## Prerequisites
- Python 3.10 or 3.11 (recommended)
- Node.js 18+ and npm 9+ for the React app
- OpenAI API key with GPT-4.1 access
- Google AI Studio key for Gemini (or adjust to another LangChain-supported backup model)

Clone the repository and open a terminal in the project root (`Math_AI/`).

## 1. Backend Setup

### 1.1 Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

### 1.2 Install Python dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3 Configure environment variables
Create a `.env` file in the project root and add the required keys:
```
OPENAI_API_KEY=<your-openai-key>
GOOGLE_API_KEY=<your-google-generative-ai-key>
# Optional: override the Gemini model LangChain should use
GOOGLE_GEMINI_MODEL=gemini-pro
```

## 2. Backend Services

### 2.1 Apply database migrations (SQLite by default)
```bash
python manage.py migrate
```

### 2.2 Run the Django development server
```bash
python manage.py runserver
```
The API is now available at `http://localhost:8000/`.

Key endpoints:
- `POST /api/evaluate/` – produces a subject-specific evaluation report from the student self-assessment JSON.
- `POST /api/ask/` – continues the tutoring conversation grounded in the stored evaluation.

During development you can inspect logs in the terminal to verify which LLM backend (GPT vs Gemini) was used.

### 2.3 Unified Knowledge + Reasoning Stack
- All three subject modules (algebra, geometry, arithmetic) now share a common `api/knowledge_hub.py` that injects:
  - A curated knowledge base plus lightweight retrieval (RAG) against subject corpora.
  - Dimension-specific few-shot exemplars.
  - An explicit chain-of-thought checklist the LLM follows before emitting final text.
- Evaluation prompts and tutor conversations automatically consume the enriched context so every response benefits from the combined techniques without additional wiring in views or front end code.

## 3. Frontend Setup

Open a second terminal (keep the backend running) and install Node dependencies:
```bash
cd frontend
npm install
```

Start the React development server:
```bash
npm start
```
The app serves at `http://localhost:3000/` and expects the backend at `http://localhost:8000/`. If you run the backend elsewhere, update the fetch URLs inside `frontend/src/pages/*.jsx`.

## 4. Typical Development Flow
- Load or enter a student self-assessment via the UI (stored in `localStorage`).
- Submit for evaluation; the backend routes to the correct subject module (algebra, arithmetic, or geometry) and stores state for follow-up questions.
- Ask follow-up questions on the Chat page; the tutor will use GPT first and fall back to Gemini if needed.

## 5. Testing and Troubleshooting
- Run backend tests (none yet, but the command scaffold is ready):
  ```bash
  python manage.py test
  ```
- If LangChain prints `SubjectClassifier` errors, verify that both API keys are present and the specified Gemini model name is valid.
- If the arithmetic module logs a warning about the retriever, install `chromadb`, `langchain-community`, and `langchain-openai` (already listed in `requirements.txt`).
- Clear browser `localStorage` or open a new incognito window if you see stale assessment data in the front end.

## 6. Production Notes
- Add a persistent database (PostgreSQL, MySQL) and update `DATABASES` in `edmaster_backend/settings.py`.
- Disable `DEBUG`, restrict `ALLOWED_HOSTS`, and review `CORS_ALLOW_ALL_ORIGINS` before deploying.
- Serve the React build (`npm run build`) via a production web server or integrate with Django static files.
