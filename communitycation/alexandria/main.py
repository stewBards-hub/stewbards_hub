import os
import asyncio
import asyncpraw
import aiosqlite
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DB_PATH = "alexandria.db"

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

class BridgeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.db = None
        self.reddit = None

    async def setup_hook(self):
        # Initialize database connection
        self.db = await aiosqlite.connect(DB_PATH)
        
        # Initialize Reddit connection
        self.reddit = asyncpraw.Reddit(
            client_id=os.getenv('client_id'),
            client_secret=os.getenv('secret'),
            username=os.getenv('username'),
            password=os.getenv('reddit_pass'),
            user_agent="Alexandria Bridge Bot"
        )

        self.subreddit = await self.reddit.subreddit("tesingshiat")
        
        # Load our bridge cogs
        await self.load_extension("discord2reddit")
        await self.load_extension("reddit2discord")
        
        print("Bridge bot is ready to sync communities!")

    async def close(self):
        # Cleanup
        if self.db:
            await self.db.close()
        if self.reddit:
            await self.reddit.close()
        await super().close()

async def main():
    bot = BridgeBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())