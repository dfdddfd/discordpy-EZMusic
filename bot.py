import discord
from discord.ext import commands
import asyncio
from youtube_search import YoutubeSearch
import youtube_dl

bot = commands.Bot(command_prefix='`')

@bot.event
async def on_ready():
    print(f'로그인 성공: {bot.user.name}!')

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {'options': '-vn'}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.id = data.get('id')
        self.uploader = data.get('uploader')
        self.uploaderid = data.get('uploader_id')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.command()
async def 들어와(msg,*,channel:discord.VoiceChannel = None):
    if channel == None:
        channel = msg.author.voice.channel
    if msg.voice_client is not None:
        await msg.voice_client.move_to(channel)
    else:
        await channel.connect()

@bot.command()
async def 나가(msg):
    await msg.voice_client.disconnect()

@bot.command() #재생
async def 재생(ctx, *, url):
    async with ctx.typing():
        player = await YTDLSource.from_url(url)
        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
    e = discord.Embed(title="재생 중!",description=player.title)
    e.set_image(url=f'https://i.ytimg.com/vi/{player.id}/hqdefault.jpg')
    await ctx.send(embed = e)

bot.run('TOKEN')
