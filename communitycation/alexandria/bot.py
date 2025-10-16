#bot.py

import asyncio 
import os 


#import asyncpraw #reddit comm
import discord
from discord.ext import commands

from dotenv import load_dotenv



import aiosqlite 
import asyncpraw

 

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

#initialize bot
description = "passes along global messages between reddit and discord!"
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', description=description, intents=intents)



reddit = asyncpraw.Reddit(
    client_id=os.getenv('client_id'), 
    client_secret=os.getenv('secret'), 
    username= os.getenv('username'), 
    password= os.getenv('reddit_pass'), 
    user_agent= "the Librarian"
)




#connect to lightweight database for message storage


@bot.event
async def on_ready(): 
    bot.db = await aiosqlite.connect("alexandria.db")

    bot.reddit = asyncpraw.Reddit(
    client_id=os.getenv('client_id'), 
    client_secret=os.getenv('secret'), 
    username= os.getenv('username'), 
    password= os.getenv('reddit_pass'), 
    user_agent= "the Librarian"
)
    bot.subreddit = await bot.reddit.subreddit("tesingshiat")
    print(f'{bot.user.name} has connected to discord and reddit!')

async def on_message(message): 
    #ignore all bots 
    if message.author.bot:  
        return
    text = message.content
    author = str(message.author)
    created_at = message.created_at 
    attachments = message.attachments 
    #downloading attachments 
    for attachment in attachments: 
        await attachments.save(f"attach")

    embeds = message.embeds
    reference = message.reference #replies or thread parent

@bot.event
async def on_thread_create(thread): 
    await   asyncio.sleep(1) #we gotta sleep to make sure the message is going to be there as well, since the content and title are sort of divorced ind discords api!
    
    parent_channel = thread.parent
    print(f"New thread created in forum: {parent_channel.name}")
    print(thread.message_count)

    #this gives us the very first message, which is just the original post content
    async for message in thread.history(limit = 1, oldest_first=True):
        message = message
        title = thread.name 
        content = message.content
        author = message.author

        submission = await bot.subreddit.submit(title = title, selftext = content)
        print("we've successfully posted to reddit!")
    #let's just try for the reddit post: 
    


@bot.event 
async def on_message_edit(message): 
    print("message has been altered! please update archive accordinly!")

@bot.command(name='global')
async def archivive(ctx, *, message: str): 
    user = str(ctx.author)
    message = message 

    print("here we go archivisizing!", ctx.author)

    #now, first, we want to save this shit to our internal database, obviously huh? 
    
#discord stuff: 


bot.run(TOKEN)


#reddit stuff: 





#subreddit.submit("")

# #dos direciones: only for stuff tagged with global or some indicator like that 
# #1. new forum entry discord -> new submission for reddit 
#     #new comment on some existing entry -> new comment on reddit as well
# #2- new submission reddit -> new discord forum entry 
#         # new comment reddit -> new comment discord; 
#         #     ----now, how to handle this nested structure here?? 
#         #     ... or, we let the discussions run their curse naturally and some ai bot just 
#         #     ocasionally summarizes whats going on? 
# # general glue, conventions and norms: 
# #     reddit tags/flags/markers partly correspond to discord channels; 
# #     in others, they're propably straight up tags? 


# # technically speaking: 
# # do we divide those into two seperate scripts that deal with the same underlying database? 
# # or just have it be one big script? 
# # how often do my reddit and discord instances/tokens or whatever need to be reinitialized? 
# # generally, is there any downtime at any point? 


# # in any case, what we've got then is: 
# # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# # reddit2discord
# # discord2reddit
# # either2databank
# # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# submission.title 
# submission.selftext #markdown 
# submission.url #link/image
# submission.media #optional dict 
# submission.preview

# comment.body 
# comment.replies
# comment.parent_id