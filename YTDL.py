import asyncio
import time
from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio, PCMVolumeTransformer

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'yes-playlist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl_format_options_info = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'yes-playlist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'dumpjson': True,
    'skip_download': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}


ffmpeg_options = {
    'options': '-vn'
}

ytdl = YoutubeDL(ytdl_format_options)
ytdl_info = YoutubeDL(ytdl_format_options_info)

class YTDLSource(PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.thumbnail = data.get('thumbnail')
        self.duration = time.strftime('%M:%S', time.gmtime(data.get('duration')))

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class YTDLInfo():
    def __init__(self, data):
        self.title = data.get('title')
        self.webpage_url = data.get('webpage_url')
        self.duration = time.strftime('%M:%S', time.gmtime(data.get('duration')))

    @classmethod
    async def get_info(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl_info.extract_info(url, download=True))

        entries = []

        if 'entries' in data:
            for entry in data['entries']:
                entries.append(cls(entry))
        else:
            entries.append(cls(data))
        
        return entries