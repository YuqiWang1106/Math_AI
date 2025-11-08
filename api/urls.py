# api/urls.py
from django.urls import path
from .views import EvaluateAPIView, AskAPIView, PreferenceClassifierAPIView

urlpatterns = [
    path("evaluate/", EvaluateAPIView.as_view()),
    path("ask/", AskAPIView.as_view()),
    path("preference/", PreferenceClassifierAPIView.as_view()),
]
