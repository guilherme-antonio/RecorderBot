from discord.ext import commands
from discord.utils import get
from discord import Embed
from discord import Colour
import json
from YTDL import YTDLInfo, YTDLSource
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.listen_channel = None
        self.history_channel = None
        self.queue = []
        self.queue_message = None
        self.current_video = None
        self.voice = None
        self.is_paused = False
        self.loop = None

    async def inactive_checker(self):
        await self.bot.wait_until_ready()

        await asyncio.sleep(60)

        if (len(self.queue) == 0 and self.current_video is None):
            await self.disconnect_from_channel()

    async def disconnect_from_channel(self):
        await self.voice.disconnect()

    def play_next(self, e):
        if e:
            print('Player error: %s' % e)
        else:
            self.bot.loop.create_task(self.play_video())

    async def play_video(self):
        if (len(self.queue) == 0):
            await self.queue_message.delete()
            self.queue_message = None
            self.current_video = None
            self.bot.loop.create_task(self.inactive_checker())
            return

        current_video_info = self.queue.pop(0)
        self.current_video = await YTDLSource.from_url(current_video_info.webpage_url, loop=False, stream=True)

        await self.show_queue()

        if (self.current_video is not None):
            self.voice.play(self.current_video, 
            after = lambda e:
            self.play_next(e))

    async def show_queue(self):
        if self.current_video is not None:
            embed = Embed(colour= Colour.gold(), title= f'[{self.current_video.duration}] - {self.current_video.title}')
            embed.set_image(url= self.current_video.thumbnail)
            embed.set_footer(text= f'{len(self.queue)} songs in queue')
        else:
            embed = Embed.Empty

        message = ''

        for index, video in enumerate(self.queue):
            message = f'{index + 1}. {video.title} [{video.duration}]\n{message}'

        if (self.queue_message is None):
            self.queue_message = await self.listen_channel.send(content= message, embed= embed)
            await self.queue_message.add_reaction('⏯️')
            await self.queue_message.add_reaction('⏹')
            await self.queue_message.add_reaction('⏭️')
        else:
            await self.queue_message.edit(content= message, embed= embed)

    async def resume(self):
        self.voice.resume()
        self.is_paused = False

    async def pause(self):
        self.voice.pause()
        self.is_paused = True

    async def stop(self):
        self.queue = []
        self.voice.stop()

    async def skip(self):
        self.voice.stop()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
                return

        if (self.listen_channel is not None and message.channel.id == self.listen_channel.id and message.content != '!listen'):
            channel = message.author.voice.channel
            voice = get(self.bot.voice_clients, guild=message.guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                voice = await channel.connect()

            self.voice = voice

            player = await YTDLInfo.get_info(message.content, loop=False)

            self.queue.append(player)
            if (self.history_channel is not None):
                await self.history_channel.send(f'{message.author.display_name} added {player.title} ({player.webpage_url})')
            
            if self.current_video is None:
                await self.play_video()
            else:
                await self.show_queue()

            await message.delete()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
                return

        if (reaction.message == self.queue_message):
            if (reaction.emoji == '⏯️'):
                if (self.is_paused):
                    await self.resume()
                else:
                    await self.pause()
            elif (reaction.emoji == '⏹'):
                await self.stop()
            elif (reaction.emoji == '⏭️'):
                await self.skip()
        
            await reaction.remove(user)

    @commands.Cog.listener()
    async def on_ready(self):
        print('on_ready start')
        await self.json_guild_config()
        print('on_ready end')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.json_guild_config(guild)

    @commands.command()
    async def config(self, ctx):
        guild = ctx.guild
        await self.json_guild_config(guild)

    async def json_guild_config(self, guild = None):
        with open('config.json') as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()

            if (guild is None):
                if 'guild' in jsonObject:
                    guild = self.bot.get_guild(jsonObject['guild'])
                else:
                    return
        
            if 'listen' not in jsonObject:
                self.listen_channel = await guild.create_text_channel(name='bot')

                jsonObject['listen'] = self.listen_channel.id
            else:
                self.listen_channel = guild.get_channel(jsonObject['listen'])

            if 'history' not in jsonObject:
                self.history_channel = await guild.create_text_channel(name='bot-history')

                jsonObject['history'] = self.history_channel.id
            else:
                self.history_channel = guild.get_channel(jsonObject['history'])

        with open('config.json', 'w') as jsonFile:
            jsonSerialized = json.dumps(jsonObject)
            jsonFile.write(jsonSerialized)

bot = commands.Bot(command_prefix='!')
bot.add_cog(Music(bot))
bot.run(os.getenv('TOKEN'))
print('End of execution')