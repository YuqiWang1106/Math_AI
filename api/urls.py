# api/urls.py
from django.urls import path
from .views import AskAPIView, EvaluateAPIView, StudentGrowthAPIView

urlpatterns = [
    path("evaluate/", EvaluateAPIView.as_view()),
    path("ask/", AskAPIView.as_view()),
    path("students/<str:student_id>/growth/", StudentGrowthAPIView.as_view()),
]
