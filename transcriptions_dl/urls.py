# transcriptions_dl/urls.py
from django.urls import path
from . import api

app_name = 'transcriptions_dl'

urlpatterns = [
    # Synchronous transcript download
    path('download/', api.download_transcript_api, name='download_transcript'),
    
    # Asynchronous transcript download
    path('download-async/', api.download_transcript_api_async, name='download_transcript_async'),
    
    # Job status checking (placeholder)
    path('status/<str:job_id>/', api.transcript_job_status, name='transcript_job_status'),
    
    # Job result retrieval (placeholder)
    path('result/<str:job_id>/', api.transcript_job_result, name='transcript_job_result'),
    
    # Transcript preview
    path('preview/', api.transcript_preview_api, name='transcript_preview'),
]
