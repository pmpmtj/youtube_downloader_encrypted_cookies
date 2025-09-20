# YouTube Downloader - Django API with Background Tasks

A Django-based YouTube audio downloader with asynchronous background processing using `django-background-tasks`.

## Features

- **Synchronous Downloads**: Immediate audio download via API
- **Asynchronous Downloads**: Background processing for long-running downloads
- **REST API**: Full RESTful API with status tracking
- **File Management**: Automatic file organization in `media/downloads/audio/`
- **No Redis Required**: Uses Django database for task storage

## Installation

1. **Clone and Setup**:
   ```powershell
   git clone <repository-url>
   cd youtube_downloader
   ```

2. **Environment Configuration**:
   ```powershell
   # Copy the example environment file
   copy .env.example .env
   
   # Edit .env with your database credentials
   notepad .env
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run Migrations**:
   ```powershell
   python manage.py migrate
   ```

5. **Create Superuser**:
   ```powershell
   python manage.py createsuperuser
   ```

6. **Start Services**:
   ```powershell
   # Terminal 1: Start Django server
   python manage.py runserver

   # Terminal 2: Start background task processor
   python manage.py process_tasks
   ```

## API Endpoints

### Synchronous Download
```powershell
# Download audio immediately
Invoke-WebRequest -Uri "http://localhost:8000/api/download-audio/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Asynchronous Download (Background Tasks)

#### 1. Queue a Download
```powershell
# Queue audio download for background processing
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/download-audio-async/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'

# Parse response to get task_id
$taskData = $response.Content | ConvertFrom-Json
$taskId = $taskData.task_id
Write-Host "Task ID: $taskId"
```

#### 2. Check Task Status
```powershell
# Check status of a background task
$taskId = "YOUR_TASK_ID_HERE"
$statusResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/" -Method GET
$statusData = $statusResponse.Content | ConvertFrom-Json
Write-Host "Status: $($statusData.status)"
Write-Host "Created: $($statusData.created_at)"
```

#### 3. Download Result File
```powershell
# Download the completed audio file
$taskId = "YOUR_TASK_ID_HERE"
$resultResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/result/" -Method GET

# Save the file
$filename = "downloaded_audio.mp3"
[System.IO.File]::WriteAllBytes($filename, $resultResponse.Content)
Write-Host "File saved as: $filename"
```

## Database Management

### Check Background Tasks in Database
```powershell
# List all background tasks
python -c "from background_task.models import Task; [print(f'ID: {t.id}, Name: {t.task_name}, Status: {t.locked_at}') for t in Task.objects.all()]"

# Check pending tasks
python -c "from background_task.models import Task; [print(f'Pending: {t.task_name}') for t in Task.objects.filter(locked_at__isnull=True)]"

# Check completed tasks
python -c "from background_task.models import Task; [print(f'Completed: {t.task_name}') for t in Task.objects.filter(locked_at__isnull=False)]"
```

### Clear Old Tasks
```powershell
# Remove all completed tasks older than 1 hour
python -c "from background_task.models import Task; from datetime import datetime, timedelta; Task.objects.filter(locked_at__isnull=False, locked_at__lt=datetime.now()-timedelta(hours=1)).delete()"

# Remove all tasks (use with caution)
python -c "from background_task.models import Task; Task.objects.all().delete()"
```

## File Management

### Check Downloaded Files
```powershell
# List all downloaded audio files
Get-ChildItem -Path "media\downloads\audio\" -Recurse | Select-Object Name, Length, LastWriteTime | Format-Table

# Get total size of downloads
$totalSize = (Get-ChildItem -Path "media\downloads\audio\" -Recurse | Measure-Object -Property Length -Sum).Sum
Write-Host "Total downloads size: $([math]::Round($totalSize/1MB, 2)) MB"
```

### Clean Up Old Files
```powershell
# Remove files older than 7 days
Get-ChildItem -Path "media\downloads\audio\" -Recurse | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Force

# Remove files larger than 100MB (adjust as needed)
Get-ChildItem -Path "media\downloads\audio\" -Recurse | Where-Object {$_.Length -gt 100MB} | Remove-Item -Force
```

## Monitoring and Logs

### Check Server Status
```powershell
# Check if Django server is running
netstat -an | findstr ":8000"

# Check if background task processor is running
tasklist | findstr python
```

### View Recent Logs
```powershell
# Check Django logs (if logging is configured)
Get-Content -Path "logs\django.log" -Tail 20

# Monitor background task processor output
python manage.py process_tasks --verbosity=2
```

## Complete Example Workflow

```powershell
# 1. Start services (run in separate terminals)
python manage.py runserver
python manage.py process_tasks

# 2. Queue a download
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/download-audio-async/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
$taskData = $response.Content | ConvertFrom-Json
$taskId = $taskData.task_id

# 3. Monitor progress
do {
    Start-Sleep -Seconds 5
    $statusResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/" -Method GET
    $statusData = $statusResponse.Content | ConvertFrom-Json
    Write-Host "Status: $($statusData.status)"
} while ($statusData.status -ne "completed")

# 4. Download the result
$resultResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/result/" -Method GET
$filename = "downloaded_$(Get-Date -Format 'yyyyMMdd_HHmmss').mp3"
[System.IO.File]::WriteAllBytes($filename, $resultResponse.Content)
Write-Host "File downloaded: $filename"
```

## Troubleshooting

### Common Issues

1. **Task not processing**: Ensure `python manage.py process_tasks` is running
2. **File not found**: Check if download completed successfully
3. **Permission errors**: Ensure write permissions to `media/downloads/audio/`

### Reset Everything
```powershell
# Stop all Python processes
taskkill /f /im python.exe

# Clear database
del db.sqlite3
python manage.py migrate

# Restart services
python manage.py runserver
python manage.py process_tasks
```

## Configuration

### Settings (youtube_downloader/settings.py)
- `BACKGROUND_TASK_RUN_ASYNC = True`: Enable async processing
- `MEDIA_ROOT`: Directory for downloaded files
- `MEDIA_URL`: URL prefix for media files

### Customization
- Modify `audio_dl/tasks.py` to customize download behavior
- Update `audio_dl/api.py` to change API responses
- Adjust file storage paths in settings

## Dependencies

- Django 5.2
- djangorestframework 3.16.1
- django-background-tasks 1.2.8
- yt-dlp 2025.9.5

## License

This project is for educational and personal use only. Please respect YouTube's terms of service and copyright laws.
