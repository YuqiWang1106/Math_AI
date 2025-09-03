# Adaptive ChatBot

A full-stack application with a Django backend and React frontend.

------------------------------------------------------------------------

## 1. Prject Structure

MATH_AI/ │── api/ \# Django app with LangChain service │──
edmaster_backend/ \# Django project config │── frontend/ \# React
frontend │── requirements.txt \# Python dependencies │── README.md \#
Project documentation

## 2. Environment Setup

1.  Create Virtual Environment\
    `python3 -m venv .venv`

2.  Activate\
    `source .venv/bin/activate` (Mac/Linux)\
    `.venv\Scripts\activate` (Windows)

3.  Install Python Dependencies\
    `pip install -r requirements.txt`

4.  Set Environment Variables

    -   Create a `.env` file in the project root (MATH_AI) and add:\
    -   `OPENAI_API_KEY=your_api_key_here`

## 3. Run Django Server

``` bash
cd edmaster_backend
python manage.py migrate   # Database is not set up
python manage.py runserver
```

## 4. Frontend Setup (React)

``` bash
cd frontend
npm install
npm start
```
