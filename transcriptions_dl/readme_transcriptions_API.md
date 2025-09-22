# Transcriptions API Documentation

A Django REST API for downloading YouTube video transcripts in multiple formats optimized for LLM analysis.

## Overview

The Transcriptions API provides endpoints to download YouTube video transcripts in 3 different formats:
- **Clean Text** - Optimized for LLM analysis with filler words removed
- **Timestamped Text** - Original format with timestamps for each segment  
- **Structured JSON** - Rich metadata with chapters, statistics, and analysis

## API Endpoints

### 1. Synchronous Transcript Download
**POST** `/transcriptions/api/download/`

Downloads transcript files immediately and returns file paths.

**Request Body:**
```json
{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "download_to_remote": false
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Transcript files downloaded successfully to server",
    "video_info": {
        "title": "Video Title",
        "uploader": "Channel Name",
        "duration": 212,
        "video_id": "dQw4w9WgXcQ"
    },
    "file_paths": {
        "clean": "/path/to/video_clean.txt",
        "timestamped": "/path/to/video_timestamped.txt",
        "structured": "/path/to/video_structured.json"
    },
    "download_source": "api"
}
```

### 2. Asynchronous Transcript Download
**POST** `/transcriptions/api/download-async/`

Queues a background task for transcript download.

**Request Body:**
```json
{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
    "task_id": "uuid-task-id",
    "status": "queued",
    "status_url": "http://localhost:8000/transcriptions/api/status/uuid-task-id/",
    "result_url": "http://localhost:8000/transcriptions/api/result/uuid-task-id/"
}
```

### 3. Transcript Preview
**GET** `/transcriptions/api/preview/?url=YOUTUBE_URL`

Preview transcript content before downloading.

**Response:**
```json
{
    "success": true,
    "video_info": {
        "title": "Video Title",
        "uploader": "Channel Name",
        "duration": 212,
        "video_id": "dQw4w9WgXcQ"
    },
    "transcript_preview": {
        "preview_text": "[0.00s] Sample transcript text...",
        "total_entries": 100,
        "statistics": {
            "word_count": 500,
            "character_count": 2500,
            "estimated_reading_time_minutes": 2.5
        }
    }
}
```

### 4. Job Status (Placeholder)
**GET** `/transcriptions/api/status/{job_id}/`

Check status of async download job.

**Response:**
```json
{
    "detail": "Status checking not implemented yet - requires database integration"
}
```

### 5. Job Result (Placeholder)
**GET** `/transcriptions/api/result/{job_id}/`

Retrieve result of completed async download.

**Response:**
```json
{
    "detail": "Result retrieval not implemented yet - requires database integration"
}
```

## PowerShell Testing Commands

### Prerequisites
- Django server running on `localhost:8000`
- Valid authentication (replace `YOUR_TOKEN` with your actual token)

### 1. Test Synchronous Download
```powershell
# Test sync download (server storage)
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    download_to_remote = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/transcriptions/api/download/" -Method POST -Body $body -ContentType "application/json" -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}
```

### 2. Test Asynchronous Download
```powershell
# Test async download (background task)
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/transcriptions/api/download-async/" -Method POST -Body $body -ContentType "application/json" -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}
```

### 3. Test Transcript Preview
```powershell
# Test transcript preview
Invoke-RestMethod -Uri "http://localhost:8000/transcriptions/api/preview/?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" -Method GET -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}
```

### 4. Test with Session Authentication
```powershell
# If using session authentication instead of token
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Login first to get session cookie
$loginBody = @{
    email = "your-email@example.com"
    password = "your-password"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/accounts/login/" -Method POST -Body $loginBody -ContentType "application/json" -WebSession $session

# Then use the session for API calls
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    download_to_remote = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/transcriptions/api/download/" -Method POST -Body $body -ContentType "application/json" -WebSession $session
```

### 5. Test Error Cases
```powershell
# Test with invalid URL
$body = @{
    url = "https://invalid-url.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/transcriptions/api/download/" -Method POST -Body $body -ContentType "application/json" -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}

# Test with missing URL
$body = @{} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/transcriptions/api/download/" -Method POST -Body $body -ContentType "application/json" -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}
```

## Complete Test Script

```powershell
# Set your base URL and authentication
$baseUrl = "http://localhost:8000"
$headers = @{"Authorization" = "Bearer YOUR_TOKEN"}  # Replace with your auth method

# Test URL
$testUrl = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

Write-Host "Testing Transcript API Endpoints..." -ForegroundColor Green

# 1. Test Preview
Write-Host "`n1. Testing Preview..." -ForegroundColor Yellow
try {
    $previewResponse = Invoke-RestMethod -Uri "$baseUrl/transcriptions/api/preview/?url=$testUrl" -Method GET -Headers $headers
    Write-Host "Preview Success: $($previewResponse.success)" -ForegroundColor Green
} catch {
    Write-Host "Preview Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Test Sync Download
Write-Host "`n2. Testing Sync Download..." -ForegroundColor Yellow
try {
    $body = @{
        url = $testUrl
        download_to_remote = $false
    } | ConvertTo-Json
    
    $syncResponse = Invoke-RestMethod -Uri "$baseUrl/transcriptions/api/download/" -Method POST -Body $body -ContentType "application/json" -Headers $headers
    Write-Host "Sync Download Success: $($syncResponse.success)" -ForegroundColor Green
    Write-Host "File Paths: $($syncResponse.file_paths | ConvertTo-Json)" -ForegroundColor Cyan
} catch {
    Write-Host "Sync Download Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Test Async Download
Write-Host "`n3. Testing Async Download..." -ForegroundColor Yellow
try {
    $body = @{
        url = $testUrl
    } | ConvertTo-Json
    
    $asyncResponse = Invoke-RestMethod -Uri "$baseUrl/transcriptions/api/download-async/" -Method POST -Body $body -ContentType "application/json" -Headers $headers
    Write-Host "Async Download Success: $($asyncResponse.status)" -ForegroundColor Green
    Write-Host "Task ID: $($asyncResponse.task_id)" -ForegroundColor Cyan
} catch {
    Write-Host "Async Download Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTesting Complete!" -ForegroundColor Green
```

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Missing 'url'"
}
```

### 400 Bad Request - Invalid URL
```json
{
    "detail": "Invalid YouTube URL"
}
```

### 400 Bad Request - Bot Detection
```json
{
    "detail": "YouTube requires authentication for this request. Please upload your YouTube cookies using the Cookie Management page."
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found - No Transcript
```json
{
    "detail": "No transcript available for this video"
}
```

### 501 Not Implemented - Placeholder Endpoints
```json
{
    "detail": "Status checking not implemented yet - requires database integration"
}
```

## Features

### Smart Transcript Selection
- Prioritizes manual transcripts over auto-generated
- English language preferred
- Automatic fallback to available languages

### Text Processing
- Filler word removal (`um`, `uh`, `like`, etc.)
- Whitespace normalization
- Transcription artifact fixing
- Chapter detection based on silence gaps

### File Formats
1. **Clean Text** (`*_clean.txt`) - LLM-optimized format
2. **Timestamped Text** (`*_timestamped.txt`) - Original format with timestamps
3. **Structured JSON** (`*_structured.json`) - Rich metadata and analysis

### Security
- Authentication required for all endpoints
- User-specific download directories
- IP and user agent tracking
- Cookie integration for YouTube authentication

## Integration

The API integrates with your existing:
- `core.downloaders.transcriptions` module
- User authentication system
- Logging and security utilities
- Cookie management system

## File Naming Convention

Files are named using the pattern:
```
{video_id}_{language_code}_{safe_title}_{format}.{extension}
```

Example:
```
dQw4w9WgXcQ_en_Rick Astley - Never Gonna Give You Up Official Vid_clean.txt
dQw4w9WgXcQ_en_Rick Astley - Never Gonna Give You Up Official Vid_timestamped.txt
dQw4w9WgXcQ_en_Rick Astley - Never Gonna Give You Up Official Vid_structured.json
```

## Notes

- **Database Integration**: Status and result endpoints are placeholders until database models are added
- **User Directories**: Files are saved to user-specific directories
- **Background Tasks**: Async downloads use `django-background-tasks`
- **Error Handling**: Comprehensive error responses with helpful guidance
- **Authentication**: Supports both token and session-based authentication

## Next Steps

1. Add database models for job tracking
2. Implement status and result endpoints
3. Add file cleanup and management
4. Add batch processing capabilities
5. Add transcript search and filtering
