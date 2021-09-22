import discord

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('-s'):
        message

client.run('ODg1MjA0NDEwNzk4NTgzODM4.YTjo2Q.U8ALmTHFU9lKSi4lm-CpNjLbBiE')