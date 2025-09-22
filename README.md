# YouTube Downloader - Django Web Application

A comprehensive Django-based YouTube downloader with both audio and video download capabilities, featuring asynchronous background processing, user authentication, and a modern web interface.

## 🚀 Features

### Core Functionality
- **Audio Downloads**: High-quality audio extraction (prefers .m4a format)
- **Video Downloads**: Full video downloads (prefers .mp4 format)
- **User Authentication**: Secure user accounts with email-based login
- **File Management**: Automatic organization in user-specific directories
- **Database Logging**: Complete download tracking and metadata storage

### Technical Features
- **Synchronous Downloads**: Immediate download via web interface
- **Asynchronous Downloads**: Background processing for long-running downloads
- **REST API**: Full RESTful API with status tracking
- **Web Interface**: Clean, responsive UI for both audio and video downloads
- **No Redis Required**: Uses Django database for task storage
- **User-Specific Storage**: Each user has their own download directories

## 📁 Project Structure

```
youtube_downloader/
├── accounts/                 # User authentication and management
│   └── cookie_views.py      # Cookie management views
├── audio_dl/                # Audio download functionality
├── video_dl/                # Video download functionality
├── cookie_management/       # Cookie management system (top-level)
│   ├── cookie_manager.py    # Core cookie functionality
│   └── commands/
│       └── cleanup_cookies.py  # Management command
├── core/                    # Core business logic and utilities
│   ├── downloaders/         # Download business logic
│   │   ├── audio/           # Audio-specific download logic
│   │   ├── video/           # Video-specific download logic
│   │   └── shared_downloader.py  # Common download functionality
│   └── shared_utils/        # Shared utilities (logging, paths, etc.)
├── templates/               # HTML templates
│   ├── audio_dl/           # Audio download templates
│   ├── video_dl/           # Video download templates
│   └── accounts/           # Authentication templates
├── media/                   # Downloaded files storage
│   └── downloads/
│       ├── audio/          # User audio downloads
│       └── video/          # User video downloads
└── logs/                   # Application logs
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) or SQLite
- Windows PowerShell (for provided commands)

### Setup Steps

1. **Clone and Navigate**:
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
   
   Example `.env` file:
   ```
   SECRET_KEY=your-secret-key-here
   DB_NAME=db_my_web_app
   DB_USER=postgres
   DB_PASSWORD=your-password
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Database Setup**:
   ```powershell
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

5. **Start Services**:
   ```powershell
   # Terminal 1: Start Django server
   python manage.py runserver
   
   # Terminal 2: Start background task processor
   python manage.py process_tasks
   ```

## 🌐 Web Interface

### Access Points
- **Main Page**: `http://127.0.0.1:8000/` (redirects to audio downloads)
- **Audio Downloads**: `http://127.0.0.1:8000/download/`
- **Video Downloads**: `http://127.0.0.1:8000/video/download/`
- **User Dashboard**: `http://127.0.0.1:8000/accounts/dashboard/`
- **Admin Interface**: `http://127.0.0.1:8000/admin/`

### Features
- **User Registration/Login**: Secure account creation and authentication
- **Download Forms**: Easy-to-use forms for both audio and video downloads
- **Download Options**: Choose to download to computer or save to server only
- **Status Tracking**: Real-time download progress monitoring
- **File Management**: View and download completed files

## 🔌 API Endpoints

### Audio Downloads

#### Synchronous Download
```powershell
# Download audio immediately
Invoke-WebRequest -Uri "http://localhost:8000/api/download-audio/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

#### Asynchronous Download
```powershell
# Queue audio download for background processing
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/download-audio-async/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
$taskData = $response.Content | ConvertFrom-Json
$taskId = $taskData.task_id
```

### Video Downloads

#### Synchronous Download
```powershell
# Download video immediately
Invoke-WebRequest -Uri "http://localhost:8000/video/api/download-video/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

#### Asynchronous Download
```powershell
# Queue video download for background processing
$response = Invoke-WebRequest -Uri "http://localhost:8000/video/api/download-video-async/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
$taskData = $response.Content | ConvertFrom-Json
$taskId = $taskData.task_id
```

### Status and Results

#### Check Task Status
```powershell
# Check status of any download task
$taskId = "YOUR_TASK_ID_HERE"
$statusResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/" -Method GET
$statusData = $statusResponse.Content | ConvertFrom-Json
Write-Host "Status: $($statusData.status)"
```

#### Download Result File
```powershell
# Download the completed file
$taskId = "YOUR_TASK_ID_HERE"
$resultResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/result/" -Method GET
$filename = "downloaded_file.mp4"  # or .m4a for audio
[System.IO.File]::WriteAllBytes($filename, $resultResponse.Content)
```

## 📊 Database Management

### Check Download Jobs
```powershell
# List all download jobs
python -c "from audio_dl.models import DownloadJob; [print(f'ID: {j.job_id}, Type: {j.download_type}, Status: {j.status}, User: {j.user.email}') for j in DownloadJob.objects.all()]"

# Check pending downloads
python -c "from audio_dl.models import DownloadJob; [print(f'Pending: {j.download_type} - {j.url}') for j in DownloadJob.objects.filter(status='pending')]"

# Check completed downloads
python -c "from audio_dl.models import DownloadJob; [print(f'Completed: {j.filename} - {j.file_size} bytes') for j in DownloadJob.objects.filter(status='completed')]"
```

### Background Task Management
```powershell
# List all background tasks
python -c "from background_task.models import Task; [print(f'ID: {t.id}, Name: {t.task_name}, Status: {t.locked_at}') for t in Task.objects.all()]"

# Clear completed tasks
python -c "from background_task.models import Task; from datetime import datetime, timedelta; Task.objects.filter(locked_at__isnull=False, locked_at__lt=datetime.now()-timedelta(hours=1)).delete()"
```

### Cookie Management Commands
```powershell
# Clean up expired cookies
python manage.py cleanup_cookies

# Check cookie management status
python -c "from cookie_management.cookie_manager import cookie_manager; print(f'Active users with cookies: {len(cookie_manager.get_all_cookie_users())}')"
```

## 📁 File Management

### Check Downloaded Files
```powershell
# List all audio files
Get-ChildItem -Path "media\downloads\audio\" -Recurse | Select-Object Name, Length, LastWriteTime | Format-Table

# List all video files
Get-ChildItem -Path "media\downloads\video\" -Recurse | Select-Object Name, Length, LastWriteTime | Format-Table

# Get total size of all downloads
$audioSize = (Get-ChildItem -Path "media\downloads\audio\" -Recurse | Measure-Object -Property Length -Sum).Sum
$videoSize = (Get-ChildItem -Path "media\downloads\video\" -Recurse | Measure-Object -Property Length -Sum).Sum
$totalSize = $audioSize + $videoSize
Write-Host "Total downloads size: $([math]::Round($totalSize/1MB, 2)) MB"
```

### Clean Up Old Files
```powershell
# Remove files older than 7 days
Get-ChildItem -Path "media\downloads\" -Recurse | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Force

# Remove files larger than 500MB (adjust as needed)
Get-ChildItem -Path "media\downloads\" -Recurse | Where-Object {$_.Length -gt 500MB} | Remove-Item -Force
```

## 🔧 Configuration

### Settings (youtube_downloader/settings.py)
- `BACKGROUND_TASK_RUN_ASYNC = True`: Enable async processing
- `MEDIA_ROOT`: Directory for downloaded files
- `MEDIA_URL`: URL prefix for media files
- `AUTH_USER_MODEL = 'accounts.User'`: Custom user model

### App Configuration (core/shared_utils/app_config.py)
- Download quality preferences
- File format settings
- Logging configuration

## 🏗️ Architecture Overview

### Module Organization

The application follows a clean, modular architecture:

- **`cookie_management/`** - Top-level cookie management system
  - Handles secure cookie storage, encryption, and retrieval
  - Provides management commands for cleanup
  - Used by all download modules for authentication

- **`core/downloaders/`** - Business logic for downloads
  - Pure download functionality without web concerns
  - Accepts cookies as parameters (decoupled from storage)
  - Handles yt-dlp integration and file processing

- **`core/shared_utils/`** - Shared utilities
  - Path resolution, logging, security, rate limiting
  - Used across all modules

- **`accounts/`** - User management and web interface
  - Authentication, user accounts, cookie management views
  - Web interface for cookie upload/management

- **`audio_dl/` & `video_dl/`** - Django apps
  - Web views, API endpoints, background tasks
  - Bridge between web interface and core downloaders
  - Handle user authentication and cookie retrieval

## 📝 Complete Example Workflow

```powershell
# 1. Start services (run in separate terminals)
python manage.py runserver
python manage.py process_tasks

# 2. Register and login via web interface
# Visit: http://127.0.0.1:8000/accounts/signup/

# 3. Download audio via web interface
# Visit: http://127.0.0.1:8000/download/

# 4. Download video via web interface
# Visit: http://127.0.0.1:8000/video/download/

# 5. Or use API for programmatic access
$response = Invoke-WebRequest -Uri "http://localhost:8000/video/api/download-video-async/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
$taskData = $response.Content | ConvertFrom-Json
$taskId = $taskData.task_id

# 6. Monitor progress
do {
    Start-Sleep -Seconds 5
    $statusResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/" -Method GET
    $statusData = $statusResponse.Content | ConvertFrom-Json
    Write-Host "Status: $($statusData.status)"
} while ($statusData.status -ne "completed")

# 7. Download the result
$resultResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$taskId/result/" -Method GET
$filename = "downloaded_$(Get-Date -Format 'yyyyMMdd_HHmmss').mp4"
[System.IO.File]::WriteAllBytes($filename, $resultResponse.Content)
Write-Host "File downloaded: $filename"
```

## 🐛 Troubleshooting

### Common Issues

1. **Task not processing**: Ensure `python manage.py process_tasks` is running
2. **File not found**: Check if download completed successfully
3. **Permission errors**: Ensure write permissions to `media/downloads/` directories
4. **Database connection**: Verify PostgreSQL credentials in `.env` file
5. **YouTube URL errors**: Ensure URLs are valid YouTube links

### Reset Everything
```powershell
# Stop all Python processes
taskkill /f /im python.exe

# Clear database (if using SQLite)
del db.sqlite3
python manage.py migrate

# Or reset PostgreSQL database
python manage.py flush

# Restart services
python manage.py runserver
python manage.py process_tasks
```

## 📦 Dependencies

- **Django 5.2**: Web framework
- **djangorestframework 3.16.1**: API framework
- **django-background-tasks 1.2.8**: Background task processing
- **yt-dlp 2025.9.5**: YouTube video/audio extraction
- **psycopg2**: PostgreSQL adapter (if using PostgreSQL)
- **python-dotenv**: Environment variable management

## 🍪 Cookie Management

### Why Use Cookies?

YouTube uses sophisticated bot detection that can block automated downloads. By uploading your browser cookies, you can:
- **Bypass bot detection**: Make your downloads appear as regular user requests
- **Access age-restricted content**: Download videos that require authentication
- **Improve download reliability**: Reduce rate limiting and blocking
- **Maintain session state**: Keep your YouTube session active during downloads

### How to Upload Cookies

#### Method 1: File Upload (Recommended)

1. **Export cookies from your browser**:
   - **Chrome/Edge**: Install "Get cookies.txt" extension
   - **Firefox**: Install "cookies.txt" extension
   
2. **Export process**:
   - Make sure you're logged into YouTube in your browser
   - Go to YouTube.com
   - Click the extension icon
   - Click "Export" and save as `cookies.txt`

3. **Upload to the application**:
   - Go to your dashboard: `http://127.0.0.1:8000/accounts/dashboard/`
   - Click "Cookie Management"
   - Select your `cookies.txt` file
   - Click "Upload Cookies"

#### Method 2: Paste Cookie Content

1. **Copy cookie content**:
   - Open your `cookies.txt` file in a text editor
   - Select all content (Ctrl+A)
   - Copy to clipboard (Ctrl+C)

2. **Paste in the application**:
   - Go to Cookie Management page
   - Paste the content in the text area
   - Click "Paste Cookies"

### Cookie Management Features

#### Security & Privacy
- **Encrypted Storage**: All cookies are encrypted using Fernet encryption
- **User-Specific**: Each user's cookies are stored separately
- **Automatic Expiry**: Cookies expire after 7 days for security
- **Secure Permissions**: Cookie files have restricted access (600 permissions)

#### Cookie Status Monitoring
- **Real-time Status**: See if cookies are active and when they expire
- **Upload History**: Track when cookies were uploaded and from which source
- **Expiry Warnings**: Get notified when cookies are about to expire
- **Easy Management**: Delete old cookies and upload new ones

#### Supported Cookie Formats
- **Netscape Format**: Standard format used by most browser extensions
- **YouTube/Google Domains**: Automatically validates YouTube and Google cookies
- **Format Validation**: Ensures cookie file is properly formatted before storage

### Cookie Management API

#### Check Cookie Status
```powershell
# Get current cookie status
$response = Invoke-WebRequest -Uri "http://localhost:8000/accounts/api/cookies/" -Method GET -Headers @{"Authorization"="Bearer YOUR_TOKEN"}
$cookieStatus = $response.Content | ConvertFrom-Json
Write-Host "Has cookies: $($cookieStatus.has_cookies)"
Write-Host "Expires: $($cookieStatus.expires_at)"
```

#### Upload Cookies via API
```powershell
# Upload cookie file via API
$cookieContent = Get-Content "cookies.txt" -Raw
$body = @{
    cookie_content = $cookieContent
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/accounts/api/cookies/" -Method POST -Headers @{"Content-Type"="application/json"; "Authorization"="Bearer YOUR_TOKEN"} -Body $body
$result = $response.Content | ConvertFrom-Json
Write-Host "Upload result: $($result.success)"
```

#### Delete Cookies
```powershell
# Delete stored cookies
$response = Invoke-WebRequest -Uri "http://localhost:8000/accounts/api/cookies/" -Method DELETE -Headers @{"Authorization"="Bearer YOUR_TOKEN"}
$result = $response.Content | ConvertFrom-Json
Write-Host "Delete result: $($result.success)"
```

### Troubleshooting Cookie Issues

#### Common Problems

1. **"No valid YouTube/Google cookies found"**:
   - Make sure you're logged into YouTube before exporting
   - Check that the cookie file contains YouTube/Google domains
   - Verify the file format is correct (Netscape format)

2. **"Invalid cookie format"**:
   - Ensure the file is in Netscape format (tab-separated values)
   - Check that the file isn't corrupted or empty
   - Make sure there are no extra characters or encoding issues

3. **"Cookies expired"**:
   - Cookies automatically expire after 7 days
   - Upload fresh cookies from your browser
   - Check the expiry date in the cookie management page

4. **Downloads still failing**:
   - Try logging out and back into YouTube in your browser
   - Export fresh cookies after logging in
   - Check if the video is age-restricted or region-locked

#### Cookie File Format Example

A valid `cookies.txt` file should look like this:
```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	abc123def456
.youtube.com	TRUE	/	FALSE	1234567890	PREF	value1=value2
.google.com	TRUE	/	FALSE	1234567890	CONSENT	YES+US.en+20231201-00-0
```

### Best Practices

1. **Regular Updates**: Upload fresh cookies every few days
2. **Browser Sync**: Use the same browser account for both exporting and downloading
3. **Privacy**: Only upload cookies from trusted devices
4. **Cleanup**: Delete old cookies when uploading new ones
5. **Testing**: Test downloads after uploading cookies to ensure they work

## 🔒 Security Notes

- User authentication is required for all downloads
- Files are stored in user-specific directories
- All downloads are logged with user tracking
- API endpoints require authentication
- **Cookie encryption**: All uploaded cookies are encrypted at rest
- **Automatic expiry**: Cookies expire after 7 days for security
- **Secure storage**: Cookie files have restricted access permissions

## 📄 License

This project is for educational and personal use only. Please respect YouTube's terms of service and copyright laws.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in the `logs/` directory
3. Check the Django admin interface for download job status
4. Create an issue in the repository