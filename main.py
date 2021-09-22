import discord
import json

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('-s'):
        await message.channel.send("Oi :P")


with open("token.json") as jsonFile:
    jsonObject = json.load(jsonFile)
    jsonFile.close()

client.run(jsonObject['token'])