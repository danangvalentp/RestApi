import requests
import os
import logging
from typing import Optional, Dict

class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram sender
        
        Args:
            bot_token: Telegram bot API token
            chat_id: Target chat ID to send videos to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    def send_video(self, video_path: str, caption: str = None) -> Optional[Dict]:
        """
        Send video file to Telegram chat
        
        Args:
            video_path: Path to the video file
            caption: Optional caption for the video
            
        Returns:
            Telegram API response or None if failed
        """
        try:
            if not os.path.exists(video_path):
                logging.error(f"Video file not found: {video_path}")
                return None
                
            # Check file size (Telegram limit is 50MB for videos)
            file_size = os.path.getsize(video_path)
            if file_size > 50 * 1024 * 1024:  # 50MB in bytes
                logging.warning(f"Video file too large for Telegram: {file_size} bytes")
                return self._send_as_document(video_path, caption)
            
            url = f"{self.base_url}/sendVideo"
            
            # Prepare the video file
            with open(video_path, 'rb') as video_file:
                files = {
                    'video': video_file
                }
                
                data = {
                    'chat_id': self.chat_id,
                    'supports_streaming': True
                }
                
                if caption:
                    data['caption'] = caption
                
                logging.info(f"Sending video to Telegram: {os.path.basename(video_path)}")
                response = requests.post(url, files=files, data=data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logging.info(f"Video sent successfully to Telegram: {os.path.basename(video_path)}")
                        return result
                    else:
                        logging.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                        return None
                else:
                    logging.error(f"HTTP error sending video: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logging.error(f"Error sending video to Telegram: {str(e)}")
            return None
    
    def _send_as_document(self, video_path: str, caption: str = None) -> Optional[Dict]:
        """
        Send large video as document if it exceeds video size limit
        
        Args:
            video_path: Path to the video file
            caption: Optional caption for the document
            
        Returns:
            Telegram API response or None if failed
        """
        try:
            url = f"{self.base_url}/sendDocument"
            
            with open(video_path, 'rb') as video_file:
                files = {
                    'document': video_file
                }
                
                data = {
                    'chat_id': self.chat_id
                }
                
                if caption:
                    data['caption'] = f"📹 {caption}\n\n⚠️ Sent as document due to size limit"
                else:
                    data['caption'] = "📹 Video file (sent as document due to size limit)"
                
                logging.info(f"Sending large video as document to Telegram: {os.path.basename(video_path)}")
                response = requests.post(url, files=files, data=data, timeout=120)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logging.info(f"Video document sent successfully to Telegram: {os.path.basename(video_path)}")
                        return result
                    else:
                        logging.error(f"Telegram API error (document): {result.get('description', 'Unknown error')}")
                        return None
                else:
                    logging.error(f"HTTP error sending document: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logging.error(f"Error sending video document to Telegram: {str(e)}")
            return None
    
    def send_message(self, message: str) -> Optional[Dict]:
        """
        Send text message to Telegram chat
        
        Args:
            message: Text message to send
            
        Returns:
            Telegram API response or None if failed
        """
        try:
            url = f"{self.base_url}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logging.info("Message sent successfully to Telegram")
                    return result
                else:
                    logging.error(f"Telegram API error (message): {result.get('description', 'Unknown error')}")
                    return None
            else:
                logging.error(f"HTTP error sending message: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error sending message to Telegram: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test if the bot token and chat ID are valid
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    bot_info = result.get('result', {})
                    logging.info(f"Telegram bot connected: {bot_info.get('username', 'Unknown')}")
                    
                    # Test sending a message to verify chat ID
                    test_message = "🤖 Video Downloader API connected successfully!"
                    message_result = self.send_message(test_message)
                    
                    if message_result:
                        logging.info("Telegram integration test successful")
                        return True
                    else:
                        logging.error("Failed to send test message - check chat ID")
                        return False
                else:
                    logging.error(f"Telegram bot token invalid: {result.get('description', 'Unknown error')}")
                    return False
            else:
                logging.error(f"HTTP error testing connection: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Error testing Telegram connection: {str(e)}")
            return False


# Global Telegram sender instance
telegram_sender = None

def initialize_telegram(bot_token: str = None, chat_id: str = None):
    """
    Initialize global Telegram sender instance
    
    Args:
        bot_token: Telegram bot API token
        chat_id: Target chat ID
    """
    global telegram_sender
    
    # Use provided values or defaults
    token = bot_token or "8182712453:AAF-w9Ben5ye7hX9UHBl-P6XMub4F6zi51k"
    target = chat_id or "7296711578"
    
    telegram_sender = TelegramSender(token, target)
    
    # Test connection
    if telegram_sender.test_connection():
        logging.info("Telegram integration initialized successfully")
        return True
    else:
        logging.error("Failed to initialize Telegram integration")
        telegram_sender = None
        return False

def send_video_to_telegram(video_path: str, video_info: Dict = None) -> bool:
    """
    Send video to Telegram using global sender instance
    
    Args:
        video_path: Path to the video file
        video_info: Optional video metadata for caption
        
    Returns:
        True if sent successfully, False otherwise
    """
    global telegram_sender
    
    if not telegram_sender:
        logging.warning("Telegram sender not initialized")
        return False
    
    # Create caption from video info
    caption = None
    if video_info:
        title = video_info.get('title', '')
        uploader = video_info.get('uploader', '')
        platform = video_info.get('platform', '').title()
        duration = video_info.get('duration')
        
        caption_parts = []
        if title:
            caption_parts.append(f"🎬 <b>{title}</b>")
        if uploader:
            caption_parts.append(f"👤 {uploader}")
        if platform:
            caption_parts.append(f"📱 {platform}")
        if duration:
            mins = duration // 60
            secs = duration % 60
            caption_parts.append(f"⏱️ {mins}:{secs:02d}")
        
        if caption_parts:
            caption = "\n".join(caption_parts)
    
    # Send video
    result = telegram_sender.send_video(video_path, caption)
    return result is not None