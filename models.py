from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class VideoRequest(db.Model):
    """Track all video requests"""
    __tablename__ = 'video_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(20), default='best')
    client_ip = db.Column(db.String(45), nullable=False)  # IPv6 support
    user_agent = db.Column(db.Text)
    request_type = db.Column(db.String(20), nullable=False)  # 'info', 'direct_url', 'download'
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    error_message = db.Column(db.Text)
    processing_time = db.Column(db.Float)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    video_info_id = db.Column(db.Integer, db.ForeignKey('video_info.id'))
    download_record_id = db.Column(db.Integer, db.ForeignKey('download_records.id'))
    
    def __repr__(self):
        return f'<VideoRequest {self.id}: {self.platform} - {self.status}>'


class VideoInfo(db.Model):
    """Store video metadata"""
    __tablename__ = 'video_info'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    uploader = db.Column(db.String(200))
    duration = db.Column(db.Integer)  # seconds
    view_count = db.Column(db.BigInteger)
    like_count = db.Column(db.BigInteger)
    thumbnail_url = db.Column(db.Text)
    platform = db.Column(db.String(50), nullable=False)
    original_url = db.Column(db.Text, nullable=False)
    upload_date = db.Column(db.String(8))  # YYYYMMDD format
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('video_id', 'platform', name='unique_video_platform'),
    )
    
    def __repr__(self):
        return f'<VideoInfo {self.id}: {self.title[:50]}...>'


class DownloadRecord(db.Model):
    """Track downloaded files"""
    __tablename__ = 'download_records'
    
    id = db.Column(db.Integer, primary_key=True)
    download_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    video_info_id = db.Column(db.Integer, db.ForeignKey('video_info.id'), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    file_extension = db.Column(db.String(10))
    quality = db.Column(db.String(20))
    format_id = db.Column(db.String(50))
    resolution = db.Column(db.String(20))
    fps = db.Column(db.Integer)
    download_count = db.Column(db.Integer, default=0)
    download_method = db.Column(db.String(20))  # 'direct_url' or 'server_download'
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    video_info = db.relationship('VideoInfo', backref='download_records')
    
    def __repr__(self):
        return f'<DownloadRecord {self.download_id}: {self.file_extension}>'


class ApiStats(db.Model):
    """Track API usage statistics"""
    __tablename__ = 'api_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    endpoint = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(50))
    request_count = db.Column(db.Integer, default=1)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    avg_processing_time = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint for daily stats per endpoint/platform
    __table_args__ = (
        db.UniqueConstraint('date', 'endpoint', 'platform', name='unique_daily_stats'),
    )
    
    def __repr__(self):
        return f'<ApiStats {self.date}: {self.endpoint} - {self.request_count} requests>'


class RateLimitLog(db.Model):
    """Track rate limiting events"""
    __tablename__ = 'rate_limit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    client_ip = db.Column(db.String(45), nullable=False)
    requests_made = db.Column(db.Integer, nullable=False)
    limit_exceeded = db.Column(db.Boolean, default=False)
    time_window = db.Column(db.Integer, nullable=False)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RateLimitLog {self.client_ip}: {self.requests_made} requests>'


# Helper functions for database operations
def get_or_create_video_info(video_data):
    """Get existing video info or create new one"""
    import hashlib
    import uuid
    
    video_id = video_data.get('video_id', '')
    platform = video_data.get('platform', '')
    title = video_data.get('title', '')
    original_url = video_data.get('webpage_url', '')
    
    if not platform:
        return None
    
    # Generate a fallback video_id if empty
    if not video_id:
        # Create a unique identifier based on title and URL
        unique_string = f"{platform}_{title}_{original_url}_{uuid.uuid4().hex[:8]}"
        video_id = hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    # Check if video already exists
    video_info = VideoInfo.query.filter_by(
        video_id=video_id,
        platform=platform
    ).first()
    
    if not video_info:
        video_info = VideoInfo(
            video_id=video_id,
            title=title,
            description=video_data.get('description', ''),
            uploader=video_data.get('uploader', ''),
            duration=video_data.get('duration', 0),
            view_count=video_data.get('view_count', 0),
            like_count=video_data.get('like_count', 0),
            thumbnail_url=video_data.get('thumbnail', ''),
            platform=platform,
            original_url=original_url,
            upload_date=video_data.get('upload_date', '')
        )
        db.session.add(video_info)
        db.session.commit()
    
    return video_info


def log_video_request(url, platform, quality, client_ip, user_agent, request_type):
    """Log a video request"""
    request_log = VideoRequest(
        url=url,
        platform=platform,
        quality=quality,
        client_ip=client_ip,
        user_agent=user_agent,
        request_type=request_type
    )
    db.session.add(request_log)
    db.session.commit()
    return request_log


def update_request_status(request_log, status, error_message=None, processing_time=None, 
                         video_info_id=None, download_record_id=None):
    """Update request status"""
    request_log.status = status
    if error_message:
        request_log.error_message = error_message
    if processing_time:
        request_log.processing_time = processing_time
    if video_info_id:
        request_log.video_info_id = video_info_id
    if download_record_id:
        request_log.download_record_id = download_record_id
    
    request_log.updated_at = datetime.utcnow()
    db.session.commit()


def update_api_stats(endpoint, platform, success=True, processing_time=None):
    """Update daily API statistics"""
    today = datetime.utcnow().date()
    
    stats = ApiStats.query.filter_by(
        date=today,
        endpoint=endpoint,
        platform=platform
    ).first()
    
    if not stats:
        stats = ApiStats(
            date=today,
            endpoint=endpoint,
            platform=platform,
            request_count=1,
            success_count=1 if success else 0,
            error_count=0 if success else 1,
            avg_processing_time=processing_time or 0
        )
        db.session.add(stats)
    else:
        stats.request_count += 1
        if success:
            stats.success_count += 1
        else:
            stats.error_count += 1
        
        # Update average processing time
        if processing_time:
            if stats.avg_processing_time:
                stats.avg_processing_time = (stats.avg_processing_time + processing_time) / 2
            else:
                stats.avg_processing_time = processing_time
        
        stats.updated_at = datetime.utcnow()
    
    db.session.commit()


def log_rate_limit_event(client_ip, requests_made, limit_exceeded, time_window):
    """Log rate limiting event"""
    rate_log = RateLimitLog(
        client_ip=client_ip,
        requests_made=requests_made,
        limit_exceeded=limit_exceeded,
        time_window=time_window
    )
    db.session.add(rate_log)
    db.session.commit()


def get_popular_videos(platform=None, limit=10):
    """Get most popular videos by request count"""
    query = db.session.query(
        VideoInfo,
        func.count(VideoRequest.id).label('request_count')
    ).join(
        VideoRequest, VideoInfo.id == VideoRequest.video_info_id
    )
    
    if platform:
        query = query.filter(VideoInfo.platform == platform)
    
    return query.group_by(VideoInfo.id)\
                .order_by(func.count(VideoRequest.id).desc())\
                .limit(limit)\
                .all()


def get_platform_stats():
    """Get statistics by platform"""
    from sqlalchemy import case
    return db.session.query(
        VideoRequest.platform,
        func.count(VideoRequest.id).label('total_requests'),
        func.sum(case((VideoRequest.status == 'success', 1), else_=0)).label('successful_requests'),
        func.avg(VideoRequest.processing_time).label('avg_processing_time')
    ).group_by(VideoRequest.platform).all()