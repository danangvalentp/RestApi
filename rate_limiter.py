import time
import logging
from typing import Dict, List
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, deque] = defaultdict(deque)
        
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if client is allowed to make a request
        
        Args:
            client_id: Unique identifier for the client (usually IP address)
            
        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests outside the time window
        while client_requests and current_time - client_requests[0] > self.time_window:
            client_requests.popleft()
        
        # Check if client has exceeded the limit
        if len(client_requests) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for client {client_id}: {len(client_requests)} requests in {self.time_window}s")
            return False
        
        return True
    
    def record_request(self, client_id: str) -> None:
        """
        Record a request for the client
        
        Args:
            client_id: Unique identifier for the client
        """
        current_time = time.time()
        self.requests[client_id].append(current_time)
        
        # Clean up old requests to prevent memory buildup
        client_requests = self.requests[client_id]
        while client_requests and current_time - client_requests[0] > self.time_window:
            client_requests.popleft()
    
    def get_client_stats(self, client_id: str) -> Dict:
        """
        Get statistics for a specific client
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Dictionary containing client statistics
        """
        current_time = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests
        while client_requests and current_time - client_requests[0] > self.time_window:
            client_requests.popleft()
        
        remaining_requests = max(0, self.max_requests - len(client_requests))
        
        # Calculate time until next request is allowed
        time_until_reset = 0
        if client_requests and len(client_requests) >= self.max_requests:
            oldest_request = client_requests[0]
            time_until_reset = max(0, self.time_window - (current_time - oldest_request))
        
        return {
            'requests_made': len(client_requests),
            'requests_remaining': remaining_requests,
            'time_until_reset': time_until_reset,
            'time_window': self.time_window
        }
    
    def cleanup_old_entries(self) -> None:
        """
        Clean up old entries to prevent memory buildup
        This should be called periodically in a production environment
        """
        current_time = time.time()
        clients_to_remove = []
        
        for client_id, client_requests in self.requests.items():
            # Remove old requests
            while client_requests and current_time - client_requests[0] > self.time_window:
                client_requests.popleft()
            
            # If no recent requests, mark client for removal
            if not client_requests:
                clients_to_remove.append(client_id)
        
        # Remove clients with no recent requests
        for client_id in clients_to_remove:
            del self.requests[client_id]
        
        logger.debug(f"Cleaned up {len(clients_to_remove)} inactive clients")
