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
- `POST /api/preference/` – classifies an open-ended learner preference into a broad domain (数学/科学/金融等) 与细分分支，供前端展示与路由。

During development you can inspect logs in the terminal to verify which LLM backend (GPT vs Gemini) was used.

### 2.3 Unified Knowledge + Reasoning Stack
- 每个“领域 + 分支”会在 SQLite 表 `api_knowledgebaseentry` 中维护一个结构化的 Knowledge Base，包含 global highlights、RAG snippet、few-shot 样例以及 CoT checklist。
- `POST /api/preference/` 在识别领域/分支的同时，会调用 LLM（`api/knowledge_base_service.py`）自动生成缺失的知识库，并缓存到数据库；之后所有请求都会直接复用缓存版本。
- `api/knowledge_hub.py` 会按当前学生的 `preference_meta` 动态拉取对应的 KB，结合检索排序后注入到各学科的评估链与对话链里，实现按需扩展的新学科支持。
- 如需人工修订知识库，可直接更新 SQLite 中对应记录或编写管理界面；更新后的内容会立即被所有流程读取。
- 新增管理命令可审查/重建知识库：`python manage.py audit_kb --domain finance --branch budgeting --auto-refresh`。命令会先调用 LLM 体检当前 JSON，若检测到占位符或缺陷则自动重新生成并写回数据库。

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
- 首先进入 Preference 页面，输入“想咨询/想规划”的自然语言描述，系统会调用 `/api/preference/` 自动识别领域与分支，并显示在后续页面的导航栏。
- 跳转到 Self-Assessment 页面，填写具体的题目与知识四维（facts/strategies/procedures/rationales）；该页面会在导航栏展示刚刚识别出的领域与分支，方便跨学科扩展。
- 提交自评后的数据保存在 `localStorage`，可立即进入 Chat 页面继续提问；后端会根据评估结果和首选学科生成上下文并回答。
- 聊天过程中仍沿用原有逻辑：优先使用 GPT，必要时回退到 Gemini。

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
