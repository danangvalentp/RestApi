import yt_dlp
import logging
import re
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        # Common headers to avoid 403 errors - updated for better compatibility
        common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Enhanced yt-dlp options with better error handling
        self.ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'format': 'best',
            'noplaylist': True,
            'http_headers': common_headers,
            'cookiefile': None,
            'no_check_certificate': True,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extract_flat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'skip_download': True,  # Only get info, don't download
        }
        
        self.ydl_opts_download = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'noplaylist': True,
            'format': 'best[height<=720]/best',
            'http_headers': common_headers,
            'cookiefile': None,
            'no_check_certificate': True,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extract_flat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }

    def get_video_info(self, url: str) -> Optional[Dict]:
        """Extract video metadata without downloading"""
        try:
            # Special handling for TikTok URLs
            opts = self.ydl_opts_info.copy()
            if 'tiktok.com' in url.lower():
                opts.update({
                    'extractor_args': {
                        'tiktok': {
                            'webpage_download_timeout': 60,
                            'api_hostname': 'api.tiktokv.com'
                        }
                    }
                })
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Extract relevant information
                video_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'duration_string': self._format_duration(info.get('duration', 0)),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'webpage_url': info.get('webpage_url', url),
                    'formats': self._extract_formats(info.get('formats', [])),
                    'video_id': info.get('id', ''),
                    'platform': self._get_platform_from_extractor(info.get('extractor', ''))
                }
                
                return video_info
                
        except Exception as e:
            logger.warning(f"Primary extraction failed for {url}: {str(e)}")
            # Try fallback method
            return self._try_fallback_extraction(url)
    
    def _try_fallback_extraction(self, url: str) -> Optional[Dict]:
        """Try multiple fallback methods for video extraction"""
        fallback_methods = [
            self._extract_with_updated_headers,
            self._extract_with_minimal_opts,
            self._extract_with_no_cookies
        ]
        
        for i, method in enumerate(fallback_methods):
            try:
                logger.info(f"Trying fallback method {i+1} for {url}")
                result = method(url)
                if result:
                    logger.info(f"Successfully extracted info using fallback method {i+1}")
                    return result
            except Exception as e:
                logger.warning(f"Fallback method {i+1} failed for {url}: {str(e)}")
                continue
        
        logger.error(f"All fallback methods failed for {url}")
        return None
    
    def _extract_with_updated_headers(self, url: str) -> Optional[Dict]:
        """Try extraction with updated headers for better compatibility"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
            'socket_timeout': 60,
            'retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            return self._format_video_info(ydl.extract_info(url, download=False), url)
    
    def _extract_with_minimal_opts(self, url: str) -> Optional[Dict]:
        """Try extraction with minimal options"""
        opts = {
            'quiet': True,
            'skip_download': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            return self._format_video_info(ydl.extract_info(url, download=False), url)
    
    def _extract_with_no_cookies(self, url: str) -> Optional[Dict]:
        """Try extraction without cookies or authentication"""
        opts = {
            'quiet': True,
            'skip_download': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'cookiefile': None,
            'no_cookies': True,
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            return self._format_video_info(ydl.extract_info(url, download=False), url)
    
    def _format_video_info(self, info, url: str) -> Optional[Dict]:
        """Format extracted info into standard video info dict"""
        if not info:
            return None
        
        # Extract or generate video ID
        video_id = info.get('id', '')
        
        # For TikTok, try to extract ID from URL if not available
        if not video_id and 'tiktok.com' in url.lower():
            video_id = self._extract_tiktok_id_from_url(url)
        
        return {
            'title': info.get('title', 'Unknown Title'),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'duration_string': self._format_duration(info.get('duration', 0)),
            'thumbnail': info.get('thumbnail', ''),
            'uploader': info.get('uploader', 'Unknown'),
            'upload_date': info.get('upload_date', ''),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'webpage_url': info.get('webpage_url', url),
            'formats': self._extract_formats(info.get('formats', [])),
            'video_id': video_id,
            'platform': self._get_platform_from_extractor(info.get('extractor', ''))
        }

    def download_video(self, url: str, quality: str = 'best', output_path: str = 'downloads') -> Optional[Dict]:
        """Download video directly using yt-dlp"""
        import os
        import uuid
        
        try:
            # Create downloads directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            # Generate unique filename
            download_id = str(uuid.uuid4())
            
            # Adjust format based on quality preference
            format_selector = self._get_format_selector(quality)
            
            # Special handling for TikTok URLs
            opts = self.ydl_opts_download.copy()
            opts.update({
                'format': format_selector,
                'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
            })
            
            if 'tiktok.com' in url.lower():
                opts.update({
                    'extractor_args': {
                        'tiktok': {
                            'webpage_download_timeout': 60,
                            'api_hostname': 'api.tiktokv.com'
                        }
                    }
                })
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # First get info to check if video exists
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Now download the video
                ydl.download([url])
                
                # Find the downloaded file
                file_extension = info.get('ext', 'mp4')
                downloaded_file = os.path.join(output_path, f'{download_id}.{file_extension}')
                
                if not os.path.exists(downloaded_file):
                    # Try to find file with different extension
                    for ext in ['mp4', 'webm', 'mkv', 'avi']:
                        test_file = os.path.join(output_path, f'{download_id}.{ext}')
                        if os.path.exists(test_file):
                            downloaded_file = test_file
                            file_extension = ext
                            break
                    else:
                        logger.error(f"Downloaded file not found: {downloaded_file}")
                        return None
                
                # Get file size
                file_size = os.path.getsize(downloaded_file)
                
                download_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'download_id': download_id,
                    'filename': os.path.basename(downloaded_file),
                    'file_path': downloaded_file,
                    'file_extension': file_extension,
                    'file_size': file_size,
                    'quality': quality,
                    'format_id': info.get('format_id', ''),
                    'resolution': info.get('resolution', 'Unknown'),
                    'fps': info.get('fps', 0),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'platform': self._get_platform_from_extractor(info.get('extractor', ''))
                }
                
                return download_info
                
        except Exception as e:
            logger.warning(f"Primary download failed for {url}: {str(e)}")
            # Try fallback download method
            return self._try_fallback_download(url, quality, output_path, download_id)
    
    def _try_fallback_download(self, url: str, quality: str, output_path: str, download_id: str) -> Optional[Dict]:
        """Try fallback download methods when primary method fails"""
        import os
        
        fallback_methods = [
            self._download_with_minimal_opts,
            self._download_with_updated_headers,
            self._download_with_basic_opts
        ]
        
        for i, method in enumerate(fallback_methods):
            try:
                logger.info(f"Trying fallback download method {i+1} for {url}")
                result = method(url, quality, output_path, download_id)
                if result:
                    logger.info(f"Successfully downloaded using fallback method {i+1}")
                    return result
            except Exception as e:
                logger.warning(f"Fallback download method {i+1} failed for {url}: {str(e)}")
                continue
        
        logger.error(f"All fallback download methods failed for {url}")
        return None
    
    def _download_with_minimal_opts(self, url: str, quality: str, output_path: str, download_id: str) -> Optional[Dict]:
        """Try download with minimal options"""
        import os
        
        # Special handling for TikTok URLs with enhanced extraction
        if 'tiktok.com' in url.lower():
            # Try different TikTok extraction approaches
            tiktok_methods = [
                self._try_tiktok_mobile_extraction,
                self._try_tiktok_api_extraction,
                self._try_tiktok_generic_extraction
            ]
            
            for method in tiktok_methods:
                try:
                    result = method(url, output_path, download_id)
                    if result and self._validate_downloaded_file(result['file_path']):
                        return result
                    elif result:
                        # Clean up invalid file
                        try:
                            os.remove(result['file_path'])
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"TikTok method {method.__name__} failed: {str(e)}")
                    continue
        else:
            # Non-TikTok URLs
            opts = {
                'quiet': True,
                'ignoreerrors': True,
                'no_check_certificate': True,
                'format': 'best[height<=720]/best',
                'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    ydl.download([url])
                    result = self._create_download_info(info, output_path, download_id)
                    if result and self._validate_downloaded_file(result['file_path']):
                        return result
                    elif result:
                        try:
                            os.remove(result['file_path'])
                        except:
                            pass
        
        return None
    
    def _try_tiktok_mobile_extraction(self, url: str, output_path: str, download_id: str) -> Optional[Dict]:
        """Try TikTok extraction with mobile user agent"""
        import os
        
        opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'format': 'best',
            'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.tiktok.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                ydl.download([url])
                return self._create_download_info(info, output_path, download_id)
        return None
    
    def _try_tiktok_api_extraction(self, url: str, output_path: str, download_id: str) -> Optional[Dict]:
        """Try TikTok extraction with API configuration"""
        import os
        
        opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'format': 'best',
            'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
            'http_headers': {
                'User-Agent': 'TikTok 26.2.0 rv:262018 (iPhone; iOS 14.4.2; en_US) Cronet',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9'
            },
            'extractor_args': {
                'tiktok': {
                    'api_hostname': 'api.tiktokv.com',
                    'webpage_download_timeout': 30
                }
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                ydl.download([url])
                return self._create_download_info(info, output_path, download_id)
        return None
    
    def _try_tiktok_generic_extraction(self, url: str, output_path: str, download_id: str) -> Optional[Dict]:
        """Try TikTok extraction with generic approach"""
        import os
        
        opts = {
            'quiet': True,
            'ignoreerrors': True,
            'format': 'worst/best',  # Sometimes lower quality works better
            'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
            'socket_timeout': 60,
            'retries': 1
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                ydl.download([url])
                return self._create_download_info(info, output_path, download_id)
        return None
    
    def _validate_downloaded_file(self, file_path: str) -> bool:
        """Validate that downloaded file is actually a video file and not HTML"""
        import os
        
        if not os.path.exists(file_path):
            return False
        
        # Check file size (HTML error pages are usually small)
        file_size = os.path.getsize(file_path)
        if file_size < 1024:  # Less than 1KB is likely not a video
            return False
        
        # Check file content to ensure it's not HTML
        try:
            with open(file_path, 'rb') as f:
                first_bytes = f.read(100).lower()
                # Check for HTML indicators
                html_indicators = [b'<html', b'<!doctype', b'<head>', b'<body>', b'<title>']
                if any(indicator in first_bytes for indicator in html_indicators):
                    return False
                
                # Check for common video file signatures
                video_signatures = [
                    b'\x00\x00\x00\x18ftypmp4',  # MP4
                    b'\x00\x00\x00\x1cftyp',     # MP4 variant
                    b'\x1a\x45\xdf\xa3',         # WebM/MKV
                    b'RIFF',                       # AVI
                ]
                
                # If it has video signatures, it's likely a video
                if any(sig in first_bytes for sig in video_signatures):
                    return True
                
                # For other cases, if it's not HTML and > 1KB, assume it's valid
                return True
                
        except Exception:
            return False
    
    def _download_with_updated_headers(self, url: str, quality: str, output_path: str, download_id: str) -> Optional[Dict]:
        """Try download with updated headers"""
        import os
        
        # Special TikTok handling
        if 'tiktok.com' in url.lower():
            opts = {
                'quiet': True,
                'ignoreerrors': True,
                'no_check_certificate': True,
                'format': 'best',
                'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.tiktok.com/'
                },
                'extractor_args': {
                    'tiktok': {
                        'api_hostname': 'api.tiktokv.com'
                    }
                }
            }
        else:
            opts = {
                'quiet': True,
                'ignoreerrors': True,
                'no_check_certificate': True,
                'format': 'best[height<=720]/best',
                'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                ydl.download([url])
                result = self._create_download_info(info, output_path, download_id)
                # Validate the downloaded file
                if result and self._validate_downloaded_file(result['file_path']):
                    return result
                else:
                    # Clean up invalid file
                    if result:
                        try:
                            os.remove(result['file_path'])
                        except:
                            pass
        return None
    
    def _download_with_basic_opts(self, url: str, quality: str, output_path: str, download_id: str) -> Optional[Dict]:
        """Try download with basic options"""
        import os
        
        opts = {
            'quiet': True,
            'format': 'worst/best',
            'outtmpl': os.path.join(output_path, f'{download_id}.%(ext)s'),
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                ydl.download([url])
                result = self._create_download_info(info, output_path, download_id)
                # Validate the downloaded file
                if result and self._validate_downloaded_file(result['file_path']):
                    return result
                else:
                    # Clean up invalid file
                    if result:
                        try:
                            os.remove(result['file_path'])
                        except:
                            pass
        return None
    
    def _create_download_info(self, info, output_path: str, download_id: str) -> Optional[Dict]:
        """Create download info dict from extracted info"""
        import os
        
        # Find the downloaded file
        file_extension = info.get('ext', 'mp4')
        downloaded_file = os.path.join(output_path, f'{download_id}.{file_extension}')
        
        if not os.path.exists(downloaded_file):
            # Try to find file with different extension
            for ext in ['mp4', 'webm', 'mkv', 'avi']:
                test_file = os.path.join(output_path, f'{download_id}.{ext}')
                if os.path.exists(test_file):
                    downloaded_file = test_file
                    file_extension = ext
                    break
        
        if not os.path.exists(downloaded_file):
            return None
        
        file_size = os.path.getsize(downloaded_file)
        
        return {
            'download_id': download_id,
            'title': info.get('title', 'Unknown Title'),
            'file_path': downloaded_file,
            'file_size': file_size,
            'file_extension': file_extension,
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail', ''),
            'uploader': info.get('uploader', 'Unknown'),
            'platform': self._get_platform_from_extractor(info.get('extractor', ''))
        }

    def get_direct_url(self, url: str, quality: str = 'best') -> Optional[Dict]:
        """Get direct download URL without downloading"""
        try:
            # Adjust format based on quality preference
            format_selector = self._get_format_selector(quality)
            
            # Special handling for TikTok URLs
            opts = self.ydl_opts_download.copy()
            opts.update({
                'format': format_selector,
            })
            
            if 'tiktok.com' in url.lower():
                opts.update({
                    'extractor_args': {
                        'tiktok': {
                            'webpage_download_timeout': 60,
                            'api_hostname': 'api.tiktokv.com'
                        }
                    }
                })
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Get the best format URL
                if 'url' in info:
                    download_url = info['url']
                elif 'formats' in info and info['formats']:
                    # Get the selected format
                    formats = info['formats']
                    selected_format = formats[-1] if formats else None
                    download_url = selected_format.get('url') if selected_format else None
                else:
                    download_url = None
                
                if not download_url:
                    return None
                
                download_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'download_url': download_url,
                    'file_extension': info.get('ext', 'mp4'),
                    'file_size': info.get('filesize') or info.get('filesize_approx', 0),
                    'quality': quality,
                    'format_id': info.get('format_id', ''),
                    'resolution': info.get('resolution', 'Unknown'),
                    'fps': info.get('fps', 0),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'platform': self._get_platform_from_extractor(info.get('extractor', ''))
                }
                
                return download_info
                
        except Exception as e:
            logger.warning(f"Primary direct URL extraction failed for {url}: {str(e)}")
            # Try fallback direct URL extraction
            return self._try_fallback_direct_url(url, quality)
    
    def _try_fallback_direct_url(self, url: str, quality: str) -> Optional[Dict]:
        """Try fallback methods for direct URL extraction"""
        fallback_methods = [
            self._direct_url_with_minimal_opts,
            self._direct_url_with_updated_headers,
            self._direct_url_with_basic_opts
        ]
        
        for i, method in enumerate(fallback_methods):
            try:
                logger.info(f"Trying fallback direct URL method {i+1} for {url}")
                result = method(url, quality)
                if result:
                    logger.info(f"Successfully extracted direct URL using fallback method {i+1}")
                    return result
            except Exception as e:
                logger.warning(f"Fallback direct URL method {i+1} failed for {url}: {str(e)}")
                continue
        
        logger.error(f"All fallback direct URL methods failed for {url}")
        return None
    
    def _direct_url_with_minimal_opts(self, url: str, quality: str) -> Optional[Dict]:
        """Try direct URL extraction with minimal options"""
        opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'format': 'best[height<=720]/best',
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                return self._extract_direct_url_info(info, quality)
        return None
    
    def _direct_url_with_updated_headers(self, url: str, quality: str) -> Optional[Dict]:
        """Try direct URL extraction with updated headers"""
        opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'format': 'best[height<=720]/best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                return self._extract_direct_url_info(info, quality)
        return None
    
    def _direct_url_with_basic_opts(self, url: str, quality: str) -> Optional[Dict]:
        """Try direct URL extraction with basic options"""
        opts = {
            'quiet': True,
            'format': 'worst/best',
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                return self._extract_direct_url_info(info, quality)
        return None
    
    def _extract_direct_url_info(self, info, quality: str) -> Optional[Dict]:
        """Extract direct URL info from extracted info"""
        if not info:
            return None
        
        # Get the best format URL
        download_url = None
        if 'url' in info:
            download_url = info['url']
        elif 'formats' in info and info['formats']:
            # Get the selected format
            formats = info['formats']
            selected_format = formats[-1] if formats else None
            download_url = selected_format.get('url') if selected_format else None
        
        if not download_url:
            return None
        
        return {
            'title': info.get('title', 'Unknown Title'),
            'download_url': download_url,
            'file_extension': info.get('ext', 'mp4'),
            'file_size': info.get('filesize') or info.get('filesize_approx', 0),
            'quality': quality,
            'format_id': info.get('format_id', ''),
            'resolution': info.get('resolution', 'Unknown'),
            'fps': info.get('fps', 0),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail', ''),
            'platform': self._get_platform_from_extractor(info.get('extractor', ''))
        }
    
    def _extract_tiktok_id_from_url(self, url: str) -> str:
        """Extract TikTok video ID from URL"""
        import re
        
        # Common TikTok URL patterns
        patterns = [
            r'tiktok\.com.*?/video/(\d+)',
            r'vm\.tiktok\.com/([A-Za-z0-9]+)',
            r'vt\.tiktok\.com/([A-Za-z0-9]+)',
            r'tiktok\.com/@[^/]+/video/(\d+)',
            r'/(\d{19,})'  # TikTok video IDs are typically 19 digits
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If no pattern matches, generate from URL hash
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def _format_duration(self, duration: int) -> str:
        """Format duration in seconds to HH:MM:SS"""
        if not duration:
            return "00:00"
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def _extract_formats(self, formats: List[Dict]) -> List[Dict]:
        """Extract available formats information"""
        if not formats:
            return []
        
        extracted_formats = []
        for fmt in formats:
            format_info = {
                'format_id': fmt.get('format_id', ''),
                'quality': fmt.get('quality', 0),
                'resolution': fmt.get('resolution', 'Unknown'),
                'fps': fmt.get('fps', 0),
                'file_extension': fmt.get('ext', 'mp4'),
                'file_size': fmt.get('filesize') or fmt.get('filesize_approx', 0),
                'format_note': fmt.get('format_note', ''),
                'vcodec': fmt.get('vcodec', 'none'),
                'acodec': fmt.get('acodec', 'none')
            }
            extracted_formats.append(format_info)
        
        return extracted_formats

    def _get_format_selector(self, quality: str) -> str:
        """Get yt-dlp format selector based on quality preference"""
        quality_map = {
            'worst': 'worst',
            'best': 'best',
            '720p': 'best[height<=720]/best',
            '480p': 'best[height<=480]/best',
            '360p': 'best[height<=360]/best',
            '240p': 'best[height<=240]/best',
            'audio': 'bestaudio'
        }
        
        return quality_map.get(quality, 'best[height<=720]/best')

    def _get_platform_from_extractor(self, extractor: str) -> str:
        """Get platform name from yt-dlp extractor"""
        extractor_lower = extractor.lower()
        
        if 'youtube' in extractor_lower:
            return 'youtube'
        elif 'tiktok' in extractor_lower:
            return 'tiktok'
        elif 'instagram' in extractor_lower:
            return 'instagram'
        else:
            return extractor_lower

    def get_supported_sites(self) -> List[str]:
        """Get list of supported sites"""
        try:
            extractors = yt_dlp.extractor.gen_extractors()
            sites = []
            for extractor in extractors:
                if hasattr(extractor, 'IE_NAME'):
                    sites.append(extractor.IE_NAME)
            return sites
        except Exception as e:
            logger.error(f"Error getting supported sites: {str(e)}")
            return ['youtube', 'tiktok', 'instagram']
