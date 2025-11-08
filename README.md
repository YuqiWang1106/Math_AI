# Health Stress Coach

Full-stack stress self-assessment and coaching platform with a Django REST backend, a React front end, and LangChain-powered LLM orchestration that blends OpenAI GPT models with Google Gemini for scientific stress guidance.

## Project Structure
```
Math_AI/
├── api/                 # Django app with LangChain prompts, evaluators, and router logic
├── edmaster_backend/    # Django project settings, URLs, and ASGI/Wsgi entrypoints
├── frontend/            # React SPA where students log stress data and chat with the coach
├── manage.py            # Django management entry point
├── requirements.txt     # Backend Python dependencies
└── README.md
```

## Prerequisites
- Python 3.10 or 3.11
- Node.js 18+ and npm 9+
- OpenAI API key (GPT-4.1+ recommended)
- Google AI Studio API key (Gemini model) or another LangChain-compatible fallback
- macOS/Linux shell commands shown below; adapt to Windows where needed

Clone the repo and open a terminal at the project root (`Math_AI/`).

## 1. Backend Setup (Django + LangChain)

1. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate            # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file alongside `manage.py`:
   ```
   OPENAI_API_KEY=<your-openai-key>
   GOOGLE_API_KEY=<your-google-generative-ai-key>
   # Optional override for the Gemini model LangChain selects
   GOOGLE_GEMINI_MODEL=gemini-1.5-pro
   ```

4. **Apply database migrations (SQLite by default)**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

   The stress-coach API is now live at `http://localhost:8000/`.

### Important Backend Endpoints
- `POST /api/evaluate/` — accepts the student’s self-assessment JSON, diagnoses gaps across facts/strategies/procedures/rationales, and stores the evaluation.
- `POST /api/ask/` — delivers adaptive coaching replies grounded in the saved self-assessment plus the LLM evaluation.

Tail logs in the same terminal to see which model responded and whether any prompt failures occurred.

## 2. Frontend Setup (React)

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the React dev server**
   ```bash
   npm start
   ```

   The UI loads at `http://localhost:3000/` and talks to the backend at `http://localhost:8000/`. If you run Django on another port or host, update the API URLs in `frontend/src/pages/*.jsx`.

### Frontend Workflow
1. Visit `http://localhost:3000/` and fill the Template page with a stress topic (facts, strategies, procedures, rationales).
2. Submit the form; the data is cached in `localStorage` and also sent to `POST /api/evaluate/`.
3. Switch to the chat view to ask follow-up questions; the React app sends each message to `POST /api/ask/`, which combines the self-assessment, evaluation JSON, and latest question to craft a 2–3 sentence response focused on stress management.

## 3. Testing
- **Backend tests** (none yet, but harness ready):
  ```bash
  python manage.py test
  ```
- **Frontend tests** (React Testing Library):
  ```bash
  cd frontend
  npm test
  ```

## 4. Troubleshooting Tips
- Missing API keys → backend returns 500 with LangChain stack traces; verify `.env` is loaded (Django reads it via `python-dotenv`).
- Repeated `SubjectClassifier` errors → confirm Gemini model string matches the API version you enabled.
- Frontend stuck with stale data → clear browser `localStorage` or run in an incognito window.
- Mixed-content errors → when deploying, serve both frontend and backend over HTTPS or use a proxy.

## 5. Production Notes
- Switch to PostgreSQL/MySQL by editing `DATABASES` in `edmaster_backend/settings.py`.
- Set `DEBUG = False`, configure `ALLOWED_HOSTS`, and tighten CORS before deploying.
- Build the React app (`npm run build`) and serve via Nginx/Apache or collect as Django static files.
- Rotate API keys frequently and store them in your deployment platform’s secret manager, not in the repo.

With these steps, a new contributor can clone the repo, configure credentials, and bring up both servers in under ten minutes. Welcome to the Health Stress Coach project!
