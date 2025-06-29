# Video Downloader API

## Overview

This is a Flask-based REST API that enables users to download videos from popular social media platforms including YouTube, TikTok, and Instagram. The application provides both video metadata extraction and download functionality with built-in rate limiting for API protection.

## System Architecture

### Backend Architecture
- **Flask Framework**: Lightweight Python web framework serving as the main application server
- **yt-dlp Integration**: Core video downloading library that handles multiple platform extraction
- **Rate Limiting System**: Custom rate limiter to prevent API abuse (10 requests per 60 seconds per IP)
- **CORS Support**: Cross-origin resource sharing enabled for frontend integration

### Frontend Architecture
- **Bootstrap Dark Theme**: Modern dark-themed UI using Bootstrap CSS framework
- **Vanilla JavaScript**: Client-side functionality for API testing interface
- **Responsive Design**: Mobile-friendly interface with responsive layout

## Key Components

### Core Modules

1. **app.py** - Main Flask application
   - Route handlers for API endpoints
   - URL validation and platform detection
   - Client IP extraction for rate limiting
   - CORS and security configuration

2. **video_downloader.py** - Video processing engine
   - yt-dlp wrapper for video extraction
   - Metadata extraction without downloading
   - Format selection and quality options
   - Multi-platform support (YouTube, TikTok, Instagram)

3. **rate_limiter.py** - API protection system
   - Time-window based rate limiting
   - Per-client request tracking
   - Configurable limits (default: 10 requests/60 seconds)

4. **main.py** - Application entry point
   - Development server configuration
   - Host and port settings

### Frontend Components

1. **templates/index.html** - API testing interface
   - Interactive form for URL input
   - Real-time API response display
   - Quality selection options
   - Bootstrap-based responsive design

2. **static/js/api-test.js** - Client-side functionality
   - URL validation
   - API request handling
   - Response formatting and display
   - Loading states and error handling

## Data Flow

1. **Video Info Request Flow**:
   - Client submits video URL through web interface or API
   - URL validation against supported platforms
   - Rate limiting check based on client IP
   - yt-dlp extracts metadata without downloading
   - Formatted response with video details returned

2. **Video Download Request Flow**:
   - Similar initial steps as info request
   - Quality/format selection applied
   - yt-dlp processes download with specified options
   - Download URL or file returned to client

## External Dependencies

### Python Libraries
- **Flask**: Web framework and HTTP request handling
- **flask-cors**: Cross-origin resource sharing support
- **yt-dlp**: Video extraction from multiple platforms
- **urllib**: URL parsing and validation

### Frontend Dependencies
- **Bootstrap CSS**: UI framework with dark theme
- **Font Awesome**: Icon library for enhanced UI

### Supported Platforms
- **YouTube**: youtube.com, youtu.be, m.youtube.com
- **TikTok**: tiktok.com, vm.tiktok.com
- **Instagram**: instagram.com

## Deployment Strategy

### Development Configuration
- Flask development server on host 0.0.0.0, port 5000
- Debug mode enabled for development
- Environment-based secret key configuration

### Production Considerations
- Secret key should be set via environment variable
- Rate limiting parameters configurable
- CORS settings may need adjustment for production domains
- Consider using production WSGI server (Gunicorn, uWSGI)

### Environment Variables
- `SESSION_SECRET`: Flask session secret key (defaults to development key)

## Recent Changes

### June 29, 2025 - Enhanced Backend Integration, Database & Robust Video Extraction
- **Enhanced CORS Configuration**: Improved CORS settings for better integration with external websites
- **Dual Download Architecture**: Implemented two download methods:
  - Direct URL method (`/api/video/direct-url`) - Fast, lightweight, direct platform URLs
  - Server download method (`/api/video/download`) - Files stored server-side with stable URLs
- **PostgreSQL Database Integration**: Added comprehensive database tracking:
  - Video metadata storage and deduplication
  - Request logging with performance metrics
  - Download tracking and file management
  - Rate limiting event logging
  - Analytics and usage statistics
- **New API Endpoints**: Added endpoints for better backend integration:
  - `/api/supported-platforms` - Get list of supported platforms with metadata
  - `/api/video/validate` - Validate URLs without processing
  - `/api/rate-limit/status` - Check current rate limit status
  - `/api/serve/<download_id>` - Serve downloaded files
  - `/api/download/status/<download_id>` - Check download status
  - `/api/analytics/stats` - Get comprehensive API usage analytics
- **Database Models**: Created structured data models:
  - VideoRequest - Track all API requests with performance data
  - VideoInfo - Store video metadata with deduplication
  - DownloadRecord - Track downloaded files and serve counts
  - ApiStats - Daily usage statistics by platform
  - RateLimitLog - Rate limiting event tracking
- **File Management**: Automatic cleanup system for downloaded files (24-hour expiration)
- **Improved yt-dlp Configuration**: Enhanced headers and platform-specific settings for better success rates
- **Integration Examples**: Created comprehensive integration examples:
  - `API_INTEGRATION.md` - Complete API documentation with integration guide
  - `examples/simple-integration.html` - JavaScript integration example
  - `examples/php-integration.php` - PHP integration example
- **Robust Video Extraction System**: Implemented comprehensive fallback mechanisms:
  - Multiple extraction methods with different configurations
  - Updated headers for better platform compatibility
  - Progressive fallback from complex to minimal options
  - Handles YouTube, TikTok, Instagram extraction failures gracefully
  - TikTok-specific improvements: mobile user agents, proper referrers, content validation
  - File validation system to detect and reject HTML error pages
- **Improved Error Handling**: Enhanced error responses and validation
- **Better Documentation**: Added detailed integration guide for multiple programming languages

## Changelog

```
Changelog:
- June 29, 2025. Initial setup
- June 29, 2025. Enhanced for backend integration with other websites
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```