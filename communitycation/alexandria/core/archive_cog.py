import discord 
from discord.ext import commands 

class ArchiveCog(commands.Cog): 
    def __init__(self, bot, db):
        self.bot = bot 
        self.db = db #connects to database where we collect all posts, comments and whatnot 

        ##on that note, interesting questions on deletability, change and accessibility/flexibility in code comment reading are being raised

    @commands.command(name='global')
    async def archive(self, ctx, *, message: str): 
        
        user = str(ctx.author)
        channel = str(ctx.channel) #needed to name, arrange and cross-post properly on reddit using dem flaging methods 
        print(ctx.var())
        # await self.db.enqeue_to_write(
        #     "INSERT INTO entry(title, body, author, platform) VALUES (?,?,?,?)",
        #     ()     )

async def setup(bot): 
    await bot.add_cog(ArchiveCog(bot=bot, db = bot.db))
    