import asyncio
from typing import Any, Optional
from datetime import datetime, timedelta

class RateLimitedQueue:
    def __init__(self, rate_limit: int = 60, burst_limit: int = 0):
        self.queue = asyncio.Queue()
        self.rate_limit = rate_limit  # seconds between posts
        self.burst_limit = burst_limit  # how many can be sent before rate limiting kicks in
        self.last_post_time: Optional[datetime] = None
        self.posts_in_window = 0
        self.window_start: Optional[datetime] = None
        
    async def put(self, item: Any) -> None:
        await self.queue.put(item)
    
    async def get(self) -> Any:
        item = await self.queue.get()
        
        now = datetime.now()
        
        # Reset window if needed
        if not self.window_start or (now - self.window_start) > timedelta(seconds=self.rate_limit):
            self.window_start = now
            self.posts_in_window = 0
        
        # Handle rate limiting
        if self.posts_in_window >= self.burst_limit > 0:
            # Calculate time to wait
            time_since_window = (now - self.window_start).total_seconds()
            if time_since_window < self.rate_limit:
                wait_time = self.rate_limit - time_since_window
                await asyncio.sleep(wait_time)
                # Reset window after waiting
                self.window_start = datetime.now()
                self.posts_in_window = 0
        
        self.posts_in_window += 1
        self.last_post_time = datetime.now()
        return item
    
    def empty(self) -> bool:
        return self.queue.empty()
    
    def qsize(self) -> int:
        return self.queue.qsize()

# Initialize queues with appropriate rate limiting
# Reddit: 1 post per 3 minutes (180s) to be extra safe with spam detection
to_reddit_queue = RateLimitedQueue(rate_limit=180, burst_limit=1)

# Discord: 5 messages per 5 seconds (1 per second) per channel
to_discord_queue = RateLimitedQueue(rate_limit=5, burst_limit=5)