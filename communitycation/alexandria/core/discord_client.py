import discord 
from discord.ext import commands 
from core import utils, sync 

class DiscordBot(commands.Bot): 
    def __init__(self, db, *args, **kwargs): 
        super().__init(*args, **kwargs)
        self.db = db

    async def setup_hook(self): 
        await self.load_extension("archive_cog")


    async def on_ready(self): 
        printf(f"Logged in as {self.user}")

    async def on_message(self, message): 
        if message.author.bot: 
            return #dont want no bot-recursion hell 
        if message.content.startswith("!global"):
            
            #new message is first stored into our internal database: 
            await self.db.enqueue_to_write(
                #please give some more thought to this huh ;) 
                "INSERT INTO entry (title, body, platform, author, created_at) VALUES (?, ?, ?, ?, ?)", 
                (None, message.content, "discord", str(message.author), message.created_at)
            )

            #then, its posted on reddit as well! 
            await sync.to_reddit_queue.put(message)