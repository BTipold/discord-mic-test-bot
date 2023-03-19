import asyncio
import discord
from discord import VoiceClient
from command import Command
from genericaudiosink import GenericAudioSink

# ---------------------------------------------------------------
# @Brief: ActiveRecording performs the actual async record, and
#   handles the upload/playback as well.
# ---------------------------------------------------------------
class ActiveRecording:
    # constructor
    def __init__(self, cmd: Command) -> None:
        self.cmd = cmd
        self.record_in_progress = False
        pass

    # checks equality by comparing the guild IDs
    def __eq__(self, other):
        return self.cmd.voice_channel.id == other.cmd.voice_channel.id
    
    async def execute(self):
        # starts recording for specified duration
        if self.cmd.duration > 0 and self.cmd.voice_channel and not self.record_in_progress:
            vc : VoiceClient = await self.cmd.voice_channel.connect()
            sink = GenericAudioSink()

            # start listening
            if vc and vc.is_connected():
                vc.listen(sink=sink, decode=True, after=lambda a, e: print(f"Exception: {e}") if e is not None else None)
                self.record_in_progress = vc.is_listening()
                if vc and self.record_in_progress:
                    await self.reply_in_channel(self.cmd.text_channel, "`Recording started`")

            # listen for duration
            await asyncio.sleep(self.cmd.duration)
            await self.stop_record(self.cmd, vc, sink)

    # stops recording and executes cmd options
    async def stop_record(self, cmd: Command, vc: VoiceClient, sink: GenericAudioSink):
        if self.record_in_progress and vc.is_listening():
            vc.stop_listening()
            sink.cleanup()
            self.record_in_progress = vc.is_listening()
            
            if cmd.file:
                await self.do_file(cmd.text_channel, sink)
            if cmd.echo:
                self.do_echo(vc, sink)
                await asyncio.sleep(cmd.duration)
            if cmd.log:
                await self.do_log(sink)
        await vc.disconnect()

    # uploads audio to discord server
    async def do_file(self, channel, sink: GenericAudioSink):
        wav_fp = sink.get_wav()
        wav_file = discord.File(wav_fp, filename="Rec.Wav")
        if wav_file:
            await self.send_file_in_channel(channel, wav_file)

    # plays the audio back in the vc
    def do_echo(self, vc: discord.VoiceClient, sink: GenericAudioSink):
        sink.buffer.seek(0)
        vc.play(discord.PCMAudio(stream=sink.buffer), after=lambda e: print(f"Exception: {e}") if e is not None else None)

    # logs the file to disk
    async def do_log(wav):
        pass

    # sends message in text channel
    async def reply_in_channel(self, channel, message):
        try:
            await channel.send(message)
        except Exception as e:
            print(e)
    
    # sends message to user in DMs
    async def reply_private(self, user, message):
        try:
            await user.send(message)
        except Exception as e:
            print(e)

    # sends file in text channel
    async def send_file_in_channel(self, channel: discord.channel.TextChannel, file: discord.file.File):
        try:
            await channel.send(file=file)
        except Exception as e:
            print(e)

