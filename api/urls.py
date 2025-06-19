# api/urls.py
from django.urls import path
from .views import EvaluateAPIView, AskAPIView

urlpatterns = [
    path("evaluate/", EvaluateAPIView.as_view()),
    path("ask/", AskAPIView.as_view()),
]
