import asyncio 
import asyncpraw 
from core import sync 

class Reddit: 
    def __init__(self, client_id, client_secret, user_agent, username, password): 
        self.reddit = asyncpraw.Reddit(
            client_id=client_id, 
            client_secret=client_secret, 
            user_agent=user_agent, 
            username=username, 
            password=password)

    async def post_from_disc_to_reddit(self): 
        while True: #what kind of scope do we want to give this loop instead perhaps? 
            message = await sync.to_reddit_queue.get()
            if message is None: 
                break 

            #let's post that shit 
            subreddit = await self.reddit.subreddit("CustodAI_n")
            await subreddit.submit(title=, selftext=)
            await asyncio.sleep(30) # we dont wan be flooding no one so lets sleep for 30 seconds 