from discord import VoiceChannel
from discord import TextChannel
from discord.abc import User
from discord.guild import Guild

class Command:
    def __init__(self) -> None:
        self.voice_channel : VoiceChannel = None
        self.text_channel : TextChannel = None
        self.user : User = None
        self.guild: Guild = None
        self.help: bool = False
        self.log: bool = False
        self.echo: bool = False
        self.file: bool = False
        self.duration: int = 5