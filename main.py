from discord.ext import commands
from discord.utils import get
import json

client = commands.Bot(command_prefix='!')

@client.command()
async def record(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    

@client.command()
async def clear(ctx, amount=5):
    await ctx.channel.purge(limit=amount)
    await ctx.send("Messages have been cleared")

with open("token.json") as jsonFile:
    jsonObject = json.load(jsonFile)
    jsonFile.close()

client.run(jsonObject['token'])