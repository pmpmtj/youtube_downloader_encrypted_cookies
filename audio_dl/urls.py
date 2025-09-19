# audio_dl/urls.py
from django.urls import path
from . import views
from . import api  # DRF-based API

urlpatterns = [
    path("", views.index, name="index"),
    path("api/download-audio/", api.download_audio_api, name="download_audio_api"),
]