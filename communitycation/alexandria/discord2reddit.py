import asyncio
import discord
from discord.ext import commands
from core import sync

class Discord2RedditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.syncing = False
        self.sync_task = None
        self.retry_count = 0
        self.MAX_RETRY_DELAY = 300  # 5 minutes max delay

    async def start_sync(self):
        """Start the sync process if not already running"""
        if not self.syncing:
            self.syncing = True
            self.sync_task = asyncio.create_task(self.sync_messages())

    async def stop_sync(self):
        """Stop the sync process"""
        if self.syncing:
            self.syncing = False
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Check for @global tag
        if message.content.startswith('@global'):
            # Remove the @global tag from content
            content = message.content[7:].strip()
            
            # Store in database first
            await self.bot.db.enqueue_to_write(
                "INSERT INTO entry (title, body, platform, author, created_at) VALUES (?, ?, ?, ?, ?)",
                (None, content, "discord", str(message.author), message.created_at)
            )

            # Queue for Reddit posting
            await sync.to_reddit_queue.put({
                'title': f'From Discord: {message.author}',
                'content': content,
                'author': str(message.author),
                'source_id': str(message.id)
            })

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        # Check if the thread has @global in its name or first message
        first_message = None

        print("we have listened en fait!")

        await asyncio.sleep(1) #give some time to have message appear!
        async for message in thread.history(limit=1, oldest_first=True):
            first_message = message

        if (thread.name.startswith('@global') or 
            (first_message and first_message.content.startswith('@global'))):
            
            content = first_message.content
            if content.startswith('@global'):
                content = content[7:].strip()

            # Queue for Reddit posting as a new submission
            await sync.to_reddit_queue.put({
                'title': thread.name.replace('@global', '').strip(),
                'content': content,
                'author': str(first_message.author),
                'source_id': str(thread.id)
            })

    async def sync_messages(self):
        """Background task to handle message syncing"""
        while self.syncing:
            try:
                # Wait for a message from the queue
                message_data = await sync.to_reddit_queue.get()
                
                try:
                    # Post to Reddit
                    submission = await self.bot.subreddit.submit(
                        title=message_data['title'],
                        selftext=message_data['content']
                    )
                    
                    # Update database with the Reddit post ID for cross-reference
                    await self.bot.db.enqueue_to_write(
                        "UPDATE entry SET reddit_id = ? WHERE source_id = ? AND platform = ?",
                        (submission.id, message_data['source_id'], 'discord')
                    )
                    
                    # Reset retry counter on success
                    self.retry_count = 0
                    
                except Exception as post_error:
                    print(f"Error posting to Reddit: {post_error}")
                    # Re-queue the message if it failed
                    if self.retry_count < 3:  # Only retry 3 times
                        await sync.to_reddit_queue.put(message_data)
                        self.retry_count += 1
                        # Exponential backoff
                        delay = min(2 ** self.retry_count, self.MAX_RETRY_DELAY)
                        await asyncio.sleep(delay)
                    else:
                        print(f"Failed to post message after 3 retries: {message_data['title']}")
                        self.retry_count = 0

            except Exception as e:
                print(f"Error in sync_messages loop: {e}")
                await asyncio.sleep(5)  # Brief pause before continuing the loop

async def setup(bot):
    cog = Discord2RedditCog(bot)
    await bot.add_cog(cog)
    await cog.start_sync()