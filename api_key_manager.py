"""
API Key Manager with automatic rotation for rate limit handling
"""
from groq import Groq
import time
from typing import Optional, List
import random


class APIKeyManager:
    """Manages multiple API keys and rotates when rate limits are hit"""
    
    def __init__(self, api_keys: List[str]):
        """Initialize with list of API keys"""
        self.api_keys = api_keys
        self.current_key_index = 0
        self.rate_limited_keys = {}  # key -> timestamp when rate limit expires
        self.client = None
        self._initialize_client()
        print(f"🔑 API Key Manager initialized with {len(api_keys)} keys")
    
    def _initialize_client(self):
        """Initialize Groq client with current key"""
        current_key = self.api_keys[self.current_key_index]
        self.client = Groq(api_key=current_key)
    
    def _is_key_available(self, key_index: int) -> bool:
        """Check if a key is available (not rate limited)"""
        key = self.api_keys[key_index]
        if key not in self.rate_limited_keys:
            return True
        
        # Check if rate limit has expired
        if time.time() >= self.rate_limited_keys[key]:
            del self.rate_limited_keys[key]
            return True
        
        return False
    
    def _rotate_to_next_key(self):
        """Rotate to the next available key"""
        # Try each key once
        for i in range(len(self.api_keys)):
            next_index = (self.current_key_index + i + 1) % len(self.api_keys)
            if self._is_key_available(next_index):
                self.current_key_index = next_index
                self._initialize_client()
                print(f"🔄 Rotated to API key #{self.current_key_index + 1}")
                return True
        
        # No keys available
        return False
    
    def _mark_key_rate_limited(self, wait_seconds: int):
        """Mark current key as rate limited"""
        key = self.api_keys[self.current_key_index]
        self.rate_limited_keys[key] = time.time() + wait_seconds
        print(f"⏸️  Key #{self.current_key_index + 1} rate limited for {wait_seconds}s")
    
    def _parse_rate_limit_time(self, error_message: str) -> int:
        """Extract wait time from rate limit error message"""
        # Example: "Please try again in 5m49.919999999s"
        import re
        
        # Look for patterns like "5m49s" or "17m44.447999999s"
        pattern = r'(\d+)m(\d+)'
        match = re.search(pattern, str(error_message))
        
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds
        
        # Default to 5 minutes if we can't parse
        return 300
    
    def chat_completion(self, messages: List[dict], **kwargs) -> Optional[str]:
        """
        Create chat completion with automatic key rotation on rate limit
        
        Args:
            messages: List of message dicts
            **kwargs: Additional arguments for Groq API
            
        Returns:
            Response content or None if all keys are rate limited
        """
        max_retries = len(self.api_keys)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                    **kwargs
                )
                return response.choices[0].message.content
            
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if 'rate_limit' in error_str.lower() or '429' in error_str:
                    wait_time = self._parse_rate_limit_time(error_str)
                    self._mark_key_rate_limited(wait_time)
                    
                    # Try to rotate to next key
                    if self._rotate_to_next_key():
                        print(f"🔁 Retrying with new API key...")
                        continue
                    else:
                        # All keys are rate limited
                        print(f"⚠️  All {len(self.api_keys)} API keys are rate limited")
                        print(f"    Waiting for next available key...")
                        
                        # Find the key that will be available soonest
                        min_wait = float('inf')
                        for key, expiry_time in self.rate_limited_keys.items():
                            wait = expiry_time - time.time()
                            if wait < min_wait:
                                min_wait = wait
                        
                        if min_wait > 0 and min_wait < 600:  # Wait up to 10 minutes
                            print(f"    Next key available in {int(min_wait)}s")
                            time.sleep(min_wait + 1)  # Wait + 1 second buffer
                            
                            # Clear expired rate limits and retry
                            self.rate_limited_keys = {}
                            self._initialize_client()
                            continue
                        else:
                            raise Exception(f"All API keys rate limited. Please try again later.")
                else:
                    # Not a rate limit error, re-raise
                    raise
        
        raise Exception("Failed after trying all API keys")
    
    def get_current_key_number(self) -> int:
        """Get current key number (1-indexed for display)"""
        return self.current_key_index + 1
    
    def get_available_keys_count(self) -> int:
        """Get number of currently available keys"""
        count = 0
        for i in range(len(self.api_keys)):
            if self._is_key_available(i):
                count += 1
        return count
