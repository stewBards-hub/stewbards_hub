import asyncio
import asyncpraw
from discord.ext import commands
from core import sync

class Reddit2DiscordCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.syncing = False
        self.sync_task = None
        self.queue_task = None
        self.retry_count = 0
        self.MAX_RETRY_DELAY = 300
        self.MONITORED_FLAIRS = ['global', 'cross-post']

    async def start_sync(self):
        """Start both the submission monitoring and queue processing"""
        if not self.syncing:
            self.syncing = True
            self.sync_task = asyncio.create_task(self.sync_posts())
            self.queue_task = asyncio.create_task(self.process_queue())

    async def stop_sync(self):
        """Stop all sync tasks"""
        if self.syncing:
            self.syncing = False
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
            if self.queue_task:
                self.queue_task.cancel()
                try:
                    await self.queue_task
                except asyncio.CancelledError:
                    pass

    async def process_submission(self, submission):
        """Process a single Reddit submission"""
        # Skip if we've already processed this submission
        exists = await self.bot.db.fetch_one(
            "SELECT id FROM entry WHERE source_id = ? AND platform = ?",
            (submission.id, "reddit")
        )
        if exists:
            return

        # Store in database
        await self.bot.db.enqueue_to_write(
            "INSERT INTO entry (title, body, platform, author, created_at, source_id) VALUES (?, ?, ?, ?, ?, ?)",
            (submission.title, submission.selftext, "reddit", str(submission.author), 
             submission.created_utc, submission.id)
        )

        # Find or create appropriate Discord channel/thread
        target_channel = None
        for channel in self.bot.get_all_channels():
            if channel.name == "global-posts":  # You can customize this
                target_channel = channel
                break

        if target_channel:
            # Create message content
            content = f"**{submission.title}**\nBy u/{submission.author}\n\n{submission.selftext}"
            
            # If channel is a forum, create thread
            if isinstance(target_channel, discord.ForumChannel):
                await target_channel.create_thread(
                    name=submission.title,
                    content=content
                )
            else:
                await target_channel.send(content)

    async def sync_posts(self):
        """Background task to sync Reddit posts to Discord"""
        while self.syncing:
            try:
                subreddit = await self.bot.reddit.subreddit("your_subreddit_name")
                
                # Get new submissions and queue them
                async for submission in subreddit.stream.submissions():
                    if hasattr(submission, 'link_flair_text') and submission.link_flair_text in self.MONITORED_FLAIRS:
                        # Queue the submission for processing
                        await sync.to_discord_queue.put({
                            'id': submission.id,
                            'title': submission.title,
                            'content': submission.selftext,
                            'author': str(submission.author),
                            'created_utc': submission.created_utc,
                            'flair': submission.link_flair_text
                        })

            except Exception as e:
                print(f"Error monitoring Reddit submissions: {e}")
                delay = min(2 ** self.retry_count, self.MAX_RETRY_DELAY)
                await asyncio.sleep(delay)
                self.retry_count += 1
                continue

            # Reset retry count on successful iteration
            self.retry_count = 0

    async def process_queue(self):
        """Process the Discord message queue"""
        while self.syncing:
            try:
                # Get submission data from queue
                submission_data = await sync.to_discord_queue.get()
                
                try:
                    # Check if we've already processed this submission
                    exists = await self.bot.db.fetch_one(
                        "SELECT id FROM entry WHERE source_id = ? AND platform = ?",
                        (submission_data['id'], "reddit")
                    )
                    
                    if not exists:
                        # Find or create appropriate Discord channel
                        target_channel = None
                        for channel in self.bot.get_all_channels():
                            if channel.name == "global-posts":
                                target_channel = channel
                                break

                        if target_channel:
                            content = (
                                f"**{submission_data['title']}**\n"
                                f"By u/{submission_data['author']}\n\n"
                                f"{submission_data['content']}"
                            )

                            # Post to Discord
                            if isinstance(target_channel, discord.ForumChannel):
                                thread = await target_channel.create_thread(
                                    name=submission_data['title'],
                                    content=content
                                )
                                message = thread.starter_message
                            else:
                                message = await target_channel.send(content)

                            # Store in database
                            await self.bot.db.enqueue_to_write(
                                "INSERT INTO entry (title, body, platform, author, created_at, source_id, discord_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (submission_data['title'], submission_data['content'], "reddit", 
                                 submission_data['author'], submission_data['created_utc'],
                                 submission_data['id'], str(message.id))
                            )

                        self.retry_count = 0  # Reset retry count on success

                except Exception as post_error:
                    print(f"Error posting to Discord: {post_error}")
                    if self.retry_count < 3:  # Only retry 3 times
                        await sync.to_discord_queue.put(submission_data)
                        self.retry_count += 1
                        delay = min(2 ** self.retry_count, self.MAX_RETRY_DELAY)
                        await asyncio.sleep(delay)
                    else:
                        print(f"Failed to post submission after 3 retries: {submission_data['title']}")
                        self.retry_count = 0

            except Exception as e:
                print(f"Error in process_queue: {e}")
                await asyncio.sleep(5)

    async def process_comments(self, submission):
        """Process comments on a Reddit submission (for future implementation)"""
        # This is where you'd implement comment syncing
        # You'd need to track parent/child relationships and create appropriate Discord thread replies
        pass

async def setup(bot):
    cog = Reddit2DiscordCog(bot)
    await bot.add_cog(cog)
    await cog.start_sync()