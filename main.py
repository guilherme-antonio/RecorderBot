import asyncio
from discord.ext import commands
from discord.utils import get
import json
from YTDLSource import YTDLSource
from video import Video

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
            return

        self.current_video = self.queue.pop(0)

        await self.show_queue()

        if (self.current_video is not None):
            self.voice.play(self.current_video.source, 
            after = lambda e:
            self.play_next(e))
        else:
            self.current_video = None

    async def show_queue(self):
        if self.current_video is not None:
            message = f"Current playing {self.current_video.title}"
        else:
            message = ""

        for index, video in enumerate(self.queue):
            message = f"{index + 1} - {video.title}\n{message}"

        if (self.queue_message is None):
            self.queue_message = await self.listen_channel.send(message)
            await self.queue_message.add_reaction('⏯️')
            await self.queue_message.add_reaction('⏹')
            await self.queue_message.add_reaction('⏭️')
        else:
            await self.queue_message.edit(content= message)

    @commands.command()
    async def config(self, ctx):
        guild = ctx.guild
        with open('config.json') as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()
        
            if 'listen' not in jsonObject:
                self.listen_channel = await guild.create_text_channel(name="bot")

                jsonObject['listen'] = self.listen_channel.id
            else:
                self.listen_channel = guild.get_channel(jsonObject['listen'])

            if 'history' not in jsonObject:
                self.history_channel = await guild.create_text_channel(name="bot-history")

                jsonObject['history'] = self.history_channel.id
            else:
                self.history_channel = guild.get_channel(jsonObject['history'])

        with open('config.json', 'w') as jsonFile:
            jsonSerialized = json.dumps(jsonObject)
            jsonFile.write(jsonSerialized)

    @commands.command()
    async def listen(self, ctx):
        self.listen_channel = ctx.message.channel
        await self.listen_channel.send('Listen channel setted')

    @commands.command()
    async def history(self, ctx):
        self.history_channel = ctx.message.channel
        await self.history_channel.send('History channel setted')

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

    #@commands.command()
    #async def clear(self, ctx, amount=5):
    #    await ctx.channel.purge(limit=amount)

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

            player, title, url = await YTDLSource.from_url(message.content, loop=False, stream=True)

            video = Video(player, title)

            self.queue.append(video)
            if (self.history_channel is not None):
                await self.history_channel.send(f'{message.author.display_name} added {title}({url})')
            
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
    async def on_guild_join(self, guild):
        with open('config.json') as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()
        
            if 'listen' not in jsonObject:
                self.listen_channel = await guild.create_text_channel(name="bot")

                jsonObject['listen'] = self.listen_channel.id
            else:
                self.listen_channel = guild.get_channel(jsonObject['listen'])

            if 'history' not in jsonObject:
                self.history_channel = await guild.create_text_channel(name="bot-history")

                jsonObject['history'] = self.history_channel.id
            else:
                self.history_channel = guild.get_channel(jsonObject['history'])

        with open('config.json', 'w') as jsonFile:
            jsonSerialized = json.dumps(jsonObject)
            jsonFile.write(jsonSerialized)


with open('token.json') as jsonFile:
    jsonObject = json.load(jsonFile)
    jsonFile.close()

bot = commands.Bot(command_prefix='!')
bot.add_cog(Music(bot))
bot.run(jsonObject['token'])