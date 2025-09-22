# transcriptions_dl/admin.py
from django.contrib import admin

# TODO: Add admin classes when database models are created
# This file is prepared for future database integration

# Example admin classes (commented out until models are created):
# from .models import TranscriptDownloadJob, TranscriptJobMetadata

# @admin.register(TranscriptDownloadJob)
# class TranscriptDownloadJobAdmin(admin.ModelAdmin):
#     list_display = ['job_id', 'user', 'url', 'status', 'created_at']
#     list_filter = ['status', 'created_at', 'download_type']
#     search_fields = ['job_id', 'user__email', 'url']
#     readonly_fields = ['job_id', 'task_id', 'created_at', 'started_at', 'completed_at']
#     ordering = ['-created_at']

# @admin.register(TranscriptJobMetadata)
# class TranscriptJobMetadataAdmin(admin.ModelAdmin):
#     list_display = ['job', 'title', 'duration', 'uploader']
#     search_fields = ['title', 'uploader']
#     readonly_fields = ['raw_metadata']