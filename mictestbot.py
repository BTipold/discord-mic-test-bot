from messagehandler import MessageHandler
from recording import ActiveRecording
from command import Command
import discord


# ---------------------------------------------------------------
# @Brief: MicTestBot is the single instance of the bot that 
#   handles multiple connections at once. 
# ---------------------------------------------------------------
class MicTestBot:
    # constructor
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.voice_states = True
        intents.messages = True
        intents.message_content = True
        client = discord.Client(intents=intents)
        self.client : discord.Client = client
        self.active_recordings : dict = {}
        self.message_handler = MessageHandler(client, lambda c: self.handle_command(c))

    # starts the bot service
    def run(self, secret_file="/data/discord-mic-test-bot/vault/secret"):
        token = ''
        with open('/data/discord-mic-test-bot/vault/secret', 'r') as file:
            token = file.read()

        if len(token) > 0:
            self.client.run(token)

    # force disconnect all recordings
    async def cleanup(self):
        for rec in self.active_recordings:
            await rec.cleanup()

    # when new command comes in, this will be called!
    async def handle_command(self, command: Command):
        if command.help == True:
            await self.reply_in_channel(command.text_channel
                , r'`usage: ./mictest --opt1 --opt2 <...>\n' +
                '\n' +
                '====== options ======\n' +
                '  --time=<n>     records for n seconds (1 .. 600)\n' +
                '  --echo         plays back recording in voice chat\n' +
                '  --file         uploads an audio file\n' +
                '  --log          logs to brians server\n' +
                '  \n' +
                'example: ./mictest --time=10 --youtube --only-me\n' +
                'example: ./mictest --echo --time=5\n' +
                'example: ./mictest --file --time=9\n`')
        
        elif not command.voice_channel:
            await self.reply_in_channel(command.text_channel, "`you are not in a voice channel...`")

        elif command.voice_channel.id in self.active_recordings:
            await self.reply_in_channel(command.text_channel, "`recording already active, please wait`")
        
        elif command.echo or command.file or command.log:
            r = ActiveRecording(command)
            self.active_recordings[command.voice_channel.id] = r
            await r.execute()
            self.active_recordings.pop(command.voice_channel.id)
        
        else:
            await self.reply_in_channel(command.text_channel, "`No option selected, use --help to see usage...`")

    # sends message in text channel
    async def reply_in_channel(self, channel, message):
        try:
            await channel.send(message)
        except Exception as e:
            print(e)
