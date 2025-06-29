# Video Downloader API - Integration Guide

## Overview
REST API untuk download video dari TikTok, YouTube, dan Instagram yang dapat diintegrasikan dengan website lain.

## Base URL
```
http://localhost:5000  # Development
https://your-domain.replit.app  # Production
```

## Download Methods

API ini menyediakan dua metode download:

1. **Direct URL** (`/api/video/direct-url`) - Mendapatkan URL download langsung dari platform
   - Lebih cepat dan ringan untuk server
   - URL mungkin memiliki waktu kedaluwarsa
   - Cocok untuk integrasi sederhana

2. **Server Download** (`/api/video/download`) - Download ke server lalu serve file
   - File disimpan di server sementara (24 jam)
   - URL download stabil dan dapat diakses berulang kali
   - Cocok untuk aplikasi yang memerlukan kontrol penuh

## Endpoints

### 1. Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703548800,
  "service": "Video Downloader API"
}
```

### 2. Supported Platforms
```http
GET /api/supported-platforms
```

**Response:**
```json
{
  "success": true,
  "platforms": {
    "youtube": {
      "name": "YouTube",
      "domains": ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"],
      "icon": "fab fa-youtube",
      "color": "#FF0000"
    },
    "tiktok": {
      "name": "TikTok",
      "domains": ["tiktok.com", "www.tiktok.com", "vm.tiktok.com"],
      "icon": "fab fa-tiktok",
      "color": "#000000"
    },
    "instagram": {
      "name": "Instagram",
      "domains": ["instagram.com", "www.instagram.com"],
      "icon": "fab fa-instagram",
      "color": "#E4405F"
    }
  }
}
```

### 3. Validate URL
```http
POST /api/video/validate
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "valid": true,
  "platform": "youtube",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

### 4. Get Video Info
```http
POST /api/video/info
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "success": true,
  "platform": "youtube",
  "data": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "description": "The official video for...",
    "duration": 212,
    "duration_string": "03:32",
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "uploader": "Rick Astley",
    "upload_date": "20091025",
    "view_count": 1000000000,
    "like_count": 12000000,
    "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "video_id": "dQw4w9WgXcQ",
    "platform": "youtube",
    "formats": [...]
  }
}
```

### 5. Get Download Link
```http
POST /api/video/download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "720p"
}
```

**Response:**
```json
{
  "success": true,
  "platform": "youtube",
  "data": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "download_url": "https://direct-download-url.mp4",
    "file_extension": "mp4",
    "file_size": 15728640,
    "quality": "720p",
    "format_id": "22",
    "resolution": "1280x720",
    "fps": 30,
    "duration": 212,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "platform": "youtube"
  }
}
```

### 6. Rate Limit Status
```http
GET /api/rate-limit/status
```

**Response:**
```json
{
  "client_ip": "192.168.1.100",
  "rate_limit": {
    "max_requests": 10,
    "time_window": 60,
    "requests_made": 3,
    "requests_remaining": 7,
    "time_until_reset": 42
  }
}
```

### 7. Analytics & Statistics
```http
GET /api/analytics/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_requests": 1250,
      "successful_requests": 1100,
      "success_rate": 88.0,
      "recent_requests_7d": 89
    },
    "platform_stats": [
      {
        "platform": "youtube",
        "total_requests": 800,
        "successful_requests": 720,
        "success_rate": 90.0,
        "avg_processing_time": 2.35
      },
      {
        "platform": "tiktok", 
        "total_requests": 300,
        "successful_requests": 250,
        "success_rate": 83.3,
        "avg_processing_time": 1.8
      }
    ],
    "popular_videos": [
      {
        "title": "Popular Video Title",
        "platform": "youtube",
        "uploader": "Channel Name",
        "request_count": 25,
        "view_count": 1000000
      }
    ]
  }
}
```

## Quality Options
- `best` - Kualitas terbaik yang tersedia
- `720p` - HD 720p
- `480p` - SD 480p  
- `360p` - SD 360p
- `240p` - SD 240p
- `worst` - Kualitas terendah
- `audio` - Audio saja

## Error Responses

### Rate Limit Exceeded (429)
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please wait before making another request."
}
```

### Invalid URL (400)
```json
{
  "error": "Unsupported platform",
  "message": "URL must be from YouTube, TikTok, or Instagram"
}
```

### Video Not Found (404)
```json
{
  "error": "Video not found", 
  "message": "Could not retrieve video information. The video may be private or unavailable."
}
```

## Integration Examples

### JavaScript (Vanilla)
```javascript
class VideoDownloaderAPI {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async validateUrl(url) {
    const response = await fetch(`${this.baseUrl}/api/video/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    return response.json();
  }

  async getVideoInfo(url) {
    const response = await fetch(`${this.baseUrl}/api/video/info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    return response.json();
  }

  async getDownloadLink(url, quality = 'best') {
    const response = await fetch(`${this.baseUrl}/api/video/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality })
    });
    return response.json();
  }
}

// Usage
const api = new VideoDownloaderAPI('http://localhost:5000');

api.getVideoInfo('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

### PHP
```php
<?php
class VideoDownloaderAPI {
    private $baseUrl;

    public function __construct($baseUrl) {
        $this->baseUrl = $baseUrl;
    }

    public function validateUrl($url) {
        return $this->makeRequest('/api/video/validate', ['url' => $url]);
    }

    public function getVideoInfo($url) {
        return $this->makeRequest('/api/video/info', ['url' => $url]);
    }

    public function getDownloadLink($url, $quality = 'best') {
        return $this->makeRequest('/api/video/download', [
            'url' => $url,
            'quality' => $quality
        ]);
    }

    private function makeRequest($endpoint, $data) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $this->baseUrl . $endpoint);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json'
        ]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        
        $response = curl_exec($ch);
        curl_close($ch);
        
        return json_decode($response, true);
    }
}

// Usage
$api = new VideoDownloaderAPI('http://localhost:5000');
$result = $api->getVideoInfo('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
print_r($result);
?>
```

### Python (Requests)
```python
import requests

class VideoDownloaderAPI:
    def __init__(self, base_url):
        self.base_url = base_url

    def validate_url(self, url):
        response = requests.post(
            f"{self.base_url}/api/video/validate",
            json={"url": url}
        )
        return response.json()

    def get_video_info(self, url):
        response = requests.post(
            f"{self.base_url}/api/video/info",
            json={"url": url}
        )
        return response.json()

    def get_download_link(self, url, quality="best"):
        response = requests.post(
            f"{self.base_url}/api/video/download",
            json={"url": url, "quality": quality}
        )
        return response.json()

# Usage
api = VideoDownloaderAPI('http://localhost:5000')
result = api.get_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
print(result)
```

## Rate Limiting
- **Limit:** 10 requests per minute per IP address
- **Window:** 60 seconds rolling window
- **Response:** HTTP 429 when limit exceeded
- **Headers:** Check rate limit status with `/api/rate-limit/status`

## CORS Configuration
API sudah dikonfigurasi dengan CORS yang memungkinkan akses dari domain manapun untuk kemudahan integrasi.

## Security Notes
- API menggunakan rate limiting untuk mencegah abuse
- Validasi URL dilakukan untuk platform yang didukung
- Error handling yang comprehensive
- Logging untuk monitoring dan debugging

## Deployment
1. Deploy di Replit dengan domain `.replit.app`
2. Gunakan environment variable `SESSION_SECRET` untuk production
3. Pastikan dependencies terinstall: `yt-dlp`, `flask-cors`