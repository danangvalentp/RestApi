import os
import logging
from flask import Flask, request, jsonify, render_template, send_file, abort
from flask_cors import CORS
from video_downloader import VideoDownloader
from rate_limiter import RateLimiter
from telegram_sender import initialize_telegram, send_video_to_telegram
import time
from urllib.parse import urlparse
import threading
from datetime import datetime, timedelta
from models import (db, VideoRequest, VideoInfo, DownloadRecord, ApiStats, RateLimitLog,
                   get_or_create_video_info, log_video_request, update_request_status,
                   update_api_stats, log_rate_limit_event, get_popular_videos, get_platform_stats)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_change_in_production")

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize database
    db.init_app(app)
else:
    logger.warning("DATABASE_URL not found, running without database")

# Configure CORS for better integration with other websites
CORS(app, 
     origins='*',  # Allow all origins for better integration
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'OPTIONS'])

# Initialize services
video_downloader = VideoDownloader()
rate_limiter = RateLimiter()

# Initialize Telegram integration
initialize_telegram()

# Store for tracking downloads (will be enhanced with database)
download_store = {}

# Create database tables if database is configured
if database_url:
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            
# Database helper functions
def use_database():
    """Check if database is available"""
    return database_url is not None

def get_client_ip():
    """Get client IP address for rate limiting"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def get_user_agent():
    """Get user agent string"""
    return request.headers.get('User-Agent', '')

def validate_url(url):
    """Validate if URL is from supported platforms"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        supported_domains = [
            'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com',
            'tiktok.com', 'www.tiktok.com', 'vm.tiktok.com',
            'instagram.com', 'www.instagram.com'
        ]
        
        return any(domain.endswith(d) or domain == d for d in supported_domains)
    except:
        return False

def get_platform_from_url(url):
    """Determine platform from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if 'youtube.com' in domain or 'youtu.be' in domain:
        return 'youtube'
    elif 'tiktok.com' in domain:
        return 'tiktok'
    elif 'instagram.com' in domain:
        return 'instagram'
    else:
        return 'unknown'

@app.route('/')
def index():
    """Serve API documentation page"""
    return render_template('index.html')

@app.route('/api/video/info', methods=['POST'])
def get_video_info():
    """Get video metadata without downloading"""
    start_time = time.time()
    client_ip = get_client_ip()
    user_agent = get_user_agent()
    request_log = None
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        
        # Log rate limit event
        if use_database():
            try:
                log_rate_limit_event(client_ip, 10, True, 60)
            except:
                pass
        
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please wait before making another request.'
        }), 429
    
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'URL is required in request body'
            }), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({
                'error': 'Invalid URL',
                'message': 'URL cannot be empty'
            }), 400
        
        if not validate_url(url):
            return jsonify({
                'error': 'Unsupported platform',
                'message': 'URL must be from YouTube, TikTok, or Instagram'
            }), 400
        
        platform = get_platform_from_url(url)
        logger.info(f"Getting video info for {platform} URL: {url}")
        
        # Log request to database
        if use_database():
            try:
                request_log = log_video_request(url, platform, 'N/A', client_ip, user_agent, 'info')
            except Exception as e:
                logger.error(f"Error logging request: {str(e)}")
        
        # Get video information
        video_info = video_downloader.get_video_info(url)
        
        processing_time = time.time() - start_time
        
        if not video_info:
            # Log failed request
            if use_database() and request_log:
                try:
                    update_request_status(request_log, 'failed', 'Video not found', processing_time)
                    update_api_stats('/api/video/info', platform, success=False, processing_time=processing_time)
                except:
                    pass
            
            return jsonify({
                'error': 'Video not found',
                'message': 'Could not retrieve video information. The video may be private or unavailable.'
            }), 404
        
        # Store video info in database and update request
        video_info_record = None
        if use_database():
            try:
                video_info_record = get_or_create_video_info(video_info)
                update_request_status(request_log, 'success', None, processing_time, video_info_record.id)
                update_api_stats('/api/video/info', platform, success=True, processing_time=processing_time)
            except Exception as e:
                logger.error(f"Error updating database: {str(e)}")
        
        # Record successful request
        rate_limiter.record_request(client_ip)
        
        return jsonify({
            'success': True,
            'platform': platform,
            'data': video_info
        })
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error getting video info: {str(e)}")
        
        # Log error
        if use_database() and request_log:
            try:
                update_request_status(request_log, 'failed', str(e), processing_time)
                update_api_stats('/api/video/info', platform if 'platform' in locals() else 'unknown', 
                                success=False, processing_time=processing_time)
            except:
                pass
        
        return jsonify({
            'error': 'Server error',
            'message': 'An error occurred while processing your request'
        }), 500

@app.route('/api/video/direct-url', methods=['POST'])
def get_direct_url():
    """Get direct download URL without downloading to server"""
    client_ip = get_client_ip()
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please wait before making another request.'
        }), 429
    
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'URL is required in request body'
            }), 400
        
        url = data['url'].strip()
        quality = data.get('quality', 'best')
        
        if not url:
            return jsonify({
                'error': 'Invalid URL',
                'message': 'URL cannot be empty'
            }), 400
        
        if not validate_url(url):
            return jsonify({
                'error': 'Unsupported platform',
                'message': 'URL must be from YouTube, TikTok, or Instagram'
            }), 400
        
        platform = get_platform_from_url(url)
        logger.info(f"Getting direct URL for {platform} URL: {url}")
        
        # Get direct download URL
        download_info = video_downloader.get_direct_url(url, quality)
        
        if not download_info:
            return jsonify({
                'error': 'Video not available',
                'message': 'Could not get direct download URL. The video may be private or unavailable.'
            }), 404
        
        # Record successful request
        rate_limiter.record_request(client_ip)
        
        return jsonify({
            'success': True,
            'platform': platform,
            'data': download_info
        })
        
    except Exception as e:
        logger.error(f"Error getting direct URL: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'An error occurred while processing your request'
        }), 500

@app.route('/api/video/download', methods=['POST'])
def download_video():
    """Download video to server and return download ID"""
    client_ip = get_client_ip()
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please wait before making another request.'
        }), 429
    
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'URL is required in request body'
            }), 400
        
        url = data['url'].strip()
        quality = data.get('quality', 'best')
        
        if not url:
            return jsonify({
                'error': 'Invalid URL',
                'message': 'URL cannot be empty'
            }), 400
        
        if not validate_url(url):
            return jsonify({
                'error': 'Unsupported platform',
                'message': 'URL must be from YouTube, TikTok, or Instagram'
            }), 400
        
        platform = get_platform_from_url(url)
        logger.info(f"Downloading video for {platform} URL: {url}")
        
        # Download video
        download_info = video_downloader.download_video(url, quality)
        
        if not download_info:
            return jsonify({
                'error': 'Video not available',
                'message': 'Could not download video. The video may be private or unavailable.'
            }), 404
        
        # Store download info in database and memory
        download_id = download_info['download_id']
        
        # Save to database if available
        if use_database():
            try:
                from models import DownloadRecord, VideoInfo, get_or_create_video_info
                
                # Get or create video info record
                video_info_record = get_or_create_video_info(download_info)
                
                # Create download record
                download_record = DownloadRecord(
                    download_id=download_id,
                    video_info_id=video_info_record.id,
                    file_path=download_info['file_path'],
                    file_size=download_info['file_size'],
                    file_extension=download_info['file_extension'],
                    quality='best',  # Could be extracted from download_info if available
                    download_method='server_download',
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                )
                
                db.session.add(download_record)
                db.session.commit()
                logger.info(f"Saved download record to database: {download_id}")
                
            except Exception as e:
                logger.error(f"Error saving download record to database: {str(e)}")
                db.session.rollback()
        
        # Also store in memory for backwards compatibility
        download_store[download_id] = {
            **download_info,
            'expires_at': datetime.now() + timedelta(hours=24),
            'download_count': 0
        }
        
        # Send video to Telegram
        try:
            video_path = download_info['file_path']
            telegram_success = send_video_to_telegram(video_path, download_info)
            if telegram_success:
                logger.info(f"Video sent to Telegram successfully: {download_id}")
            else:
                logger.warning(f"Failed to send video to Telegram: {download_id}")
        except Exception as e:
            logger.error(f"Error sending video to Telegram: {str(e)}")
        
        # Record successful request
        rate_limiter.record_request(client_ip)
        
        # Return info with download URL
        response_data = download_info.copy()
        response_data['download_url'] = f"/api/serve/{download_id}"
        del response_data['file_path']  # Don't expose file path
        
        return jsonify({
            'success': True,
            'platform': platform,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'An error occurred while processing your request'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = 'connected' if use_database() else 'not_configured'
    
    if use_database():
        try:
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time()),
        'service': 'Video Downloader API',
        'database': db_status
    })

@app.route('/api/supported-platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported video platforms"""
    platforms = {
        'youtube': {
            'name': 'YouTube',
            'domains': ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com'],
            'icon': 'fab fa-youtube',
            'color': '#FF0000'
        },
        'tiktok': {
            'name': 'TikTok', 
            'domains': ['tiktok.com', 'www.tiktok.com', 'vm.tiktok.com'],
            'icon': 'fab fa-tiktok',
            'color': '#000000'
        },
        'instagram': {
            'name': 'Instagram',
            'domains': ['instagram.com', 'www.instagram.com'],
            'icon': 'fab fa-instagram',
            'color': '#E4405F'
        }
    }
    
    return jsonify({
        'success': True,
        'platforms': platforms
    })

@app.route('/api/video/validate', methods=['POST'])
def validate_video_url():
    """Validate video URL without processing"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'URL is required in request body'
            }), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({
                'valid': False,
                'error': 'URL cannot be empty'
            })
        
        is_valid = validate_url(url)
        platform = get_platform_from_url(url) if is_valid else None
        
        return jsonify({
            'valid': is_valid,
            'platform': platform,
            'url': url
        })
        
    except Exception as e:
        logger.error(f"Error validating URL: {str(e)}")
        return jsonify({
            'valid': False,
            'error': 'Invalid URL format'
        })

@app.route('/api/rate-limit/status', methods=['GET'])
def get_rate_limit_status():
    """Get current rate limit status for client"""
    client_ip = get_client_ip()
    stats = rate_limiter.get_client_stats(client_ip)
    
    return jsonify({
        'client_ip': client_ip,
        'rate_limit': {
            'max_requests': rate_limiter.max_requests,
            'time_window': rate_limiter.time_window,
            'requests_made': stats['requests_made'],
            'requests_remaining': stats['requests_remaining'],
            'time_until_reset': stats['time_until_reset']
        }
    })

@app.route('/api/analytics/stats', methods=['GET'])
def get_analytics_stats():
    """Get API usage analytics"""
    if not use_database():
        return jsonify({
            'error': 'Database not available',
            'message': 'Analytics require database connection'
        }), 503
    
    try:
        # Get platform statistics
        platform_stats = get_platform_stats()
        
        # Get popular videos
        popular_videos = get_popular_videos(limit=10)
        
        # Get recent requests count
        recent_requests = db.session.query(VideoRequest)\
            .filter(VideoRequest.created_at >= datetime.utcnow() - timedelta(days=7))\
            .count()
        
        # Get success rate
        total_requests = db.session.query(VideoRequest).count()
        successful_requests = db.session.query(VideoRequest)\
            .filter(VideoRequest.status == 'success').count()
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'success_rate': round(success_rate, 2),
                    'recent_requests_7d': recent_requests
                },
                'platform_stats': [
                    {
                        'platform': stat.platform,
                        'total_requests': stat.total_requests,
                        'successful_requests': stat.successful_requests,
                        'success_rate': round((stat.successful_requests / stat.total_requests * 100) if stat.total_requests > 0 else 0, 2),
                        'avg_processing_time': round(stat.avg_processing_time, 3) if stat.avg_processing_time else 0
                    }
                    for stat in platform_stats
                ],
                'popular_videos': [
                    {
                        'title': video.VideoInfo.title,
                        'platform': video.VideoInfo.platform,
                        'uploader': video.VideoInfo.uploader,
                        'request_count': video.request_count,
                        'view_count': video.VideoInfo.view_count
                    }
                    for video in popular_videos
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'An error occurred while retrieving analytics'
        }), 500

@app.route('/api/serve/<download_id>')
def serve_video(download_id):
    """Serve downloaded video file"""
    try:
        download_info = None
        
        # First check database if available
        if use_database():
            try:
                from models import DownloadRecord
                download_record = db.session.query(DownloadRecord)\
                    .filter(DownloadRecord.download_id == download_id)\
                    .first()
                
                if download_record:
                    # Check if download has expired
                    if datetime.utcnow() > download_record.expires_at:
                        # Clean up expired download
                        try:
                            if os.path.exists(download_record.file_path):
                                os.remove(download_record.file_path)
                        except:
                            pass
                        db.session.delete(download_record)
                        db.session.commit()
                        abort(404)
                    
                    # Check if file still exists
                    if not os.path.exists(download_record.file_path):
                        db.session.delete(download_record)
                        db.session.commit()
                        abort(404)
                    
                    # Increment download count
                    download_record.download_count += 1
                    db.session.commit()
                    
                    # Get video info for title
                    video_title = download_record.video_info.title if download_record.video_info else "video"
                    
                    # Serve the file
                    return send_file(
                        download_record.file_path,
                        as_attachment=True,
                        download_name=f"{video_title}.{download_record.file_extension}",
                        mimetype='application/octet-stream'
                    )
                    
            except Exception as e:
                logger.error(f"Database error serving video {download_id}: {str(e)}")
        
        # Fallback to memory store
        if download_id not in download_store:
            abort(404)
        
        download_info = download_store[download_id]
        
        # Check if download has expired
        if datetime.now() > download_info['expires_at']:
            # Clean up expired download
            try:
                if os.path.exists(download_info['file_path']):
                    os.remove(download_info['file_path'])
            except:
                pass
            del download_store[download_id]
            abort(404)
        
        # Check if file still exists
        if not os.path.exists(download_info['file_path']):
            del download_store[download_id]
            abort(404)
        
        # Increment download count
        download_store[download_id]['download_count'] += 1
        
        # Serve the file
        return send_file(
            download_info['file_path'],
            as_attachment=True,
            download_name=f"{download_info['title']}.{download_info['file_extension']}",
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error serving video {download_id}: {str(e)}")
        abort(500)

@app.route('/api/download/status/<download_id>')
def get_download_status(download_id):
    """Get download status and info"""
    try:
        if download_id not in download_store:
            return jsonify({
                'error': 'Download not found',
                'message': 'Download ID not found or expired'
            }), 404
        
        download_info = download_store[download_id]
        
        # Check if download has expired
        if datetime.now() > download_info['expires_at']:
            del download_store[download_id]
            return jsonify({
                'error': 'Download expired',
                'message': 'Download has expired'
            }), 404
        
        # Return status info
        status_info = {
            'download_id': download_id,
            'title': download_info['title'],
            'file_extension': download_info['file_extension'],
            'file_size': download_info['file_size'],
            'quality': download_info['quality'],
            'platform': download_info['platform'],
            'download_count': download_info['download_count'],
            'expires_at': download_info['expires_at'].isoformat(),
            'download_url': f"/api/serve/{download_id}"
        }
        
        return jsonify({
            'success': True,
            'data': status_info
        })
        
    except Exception as e:
        logger.error(f"Error getting download status {download_id}: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'An error occurred while getting download status'
        }), 500

def cleanup_expired_downloads():
    """Clean up expired downloads (should be run periodically)"""
    try:
        current_time = datetime.now()
        expired_ids = []
        
        for download_id, download_info in download_store.items():
            if current_time > download_info['expires_at']:
                expired_ids.append(download_id)
                # Delete file
                try:
                    if os.path.exists(download_info['file_path']):
                        os.remove(download_info['file_path'])
                        logger.info(f"Deleted expired file: {download_info['file_path']}")
                except Exception as e:
                    logger.error(f"Error deleting expired file: {str(e)}")
        
        # Remove from store
        for download_id in expired_ids:
            del download_store[download_id]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired downloads")
            
    except Exception as e:
        logger.error(f"Error cleaning up expired downloads: {str(e)}")

# Start cleanup thread
def start_cleanup_thread():
    def cleanup_loop():
        while True:
            cleanup_expired_downloads()
            time.sleep(3600)  # Run every hour
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()

# Start cleanup when app starts
start_cleanup_thread()

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
