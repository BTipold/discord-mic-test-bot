from command import Command
import discord

# ---------------------------------------------------------------
# @Brief: Removes first and last chars if they are spaces.
# @Param: string - input string.
# @Return: clean_string - returns the string without the spaces.
# ---------------------------------------------------------------
def remove_leading_tailing_spaces(string):
    clean_string = string

    # If first character is a space, remove it
    if len(clean_string) > 0:
        if clean_string[0] == ' ':
            clean_string = clean_string[1:]

    # If last character is a space, remove it
    if len(clean_string) > 0:
        if clean_string[-1] == ' ':
            clean_string = clean_string[:-1]

    return clean_string

# ---------------------------------------------------------------
# @Brief: If there are long strings of spaces in a string, they
#   will be replaced by a single space. If there are spaces at
#   the beginning or end of a string, they will also be removed.
# @Param: string - input string.
# @Return: clean_string - returns the string without the spaces.
# ---------------------------------------------------------------
def remove_white_spaces(string):
    clean_string = ''
    num_of_spaces = 0

    for char in string:
        # If its a space, only copy the first
        if char == ' ':
            if num_of_spaces < 1:
                clean_string += char
            num_of_spaces += 1

        # If its a letter or number, copy and reset count
        else:
            clean_string += char
            num_of_spaces = 0

    # Remove first and last space.
    clean_string = remove_leading_tailing_spaces(clean_string)

    return clean_string

# ---------------------------------------------------------------
# @Brief: MessageHandler receives all text messages from all 
#   servers. If any commands are requested, the callback will
#   be triggered. 
# @Attributes:
#   client: discord.Client
#   callback: lambda: c:Command -> None
# ---------------------------------------------------------------
class MessageHandler:
    # constructor
    def __init__(self, client: discord.Client, callback) -> None:
        self.client = client
        self.callback = callback

        # proxy events
        @self.client.event
        async def on_ready():
            print("Mic Test Bot Ready")
    
        @self.client.event
        async def on_message(message):
            return await self.handle_message(message)

    # handles command line arguments and triggers callback if there are any valid commands
    async def handle_message(self, message: discord.message.Message) -> None:
        if message.author == self.client.user:
            return

        text = str(message.content)
        
        # if valid
        if text and len(text) >= 8:

            # parse command
            c = self.parse_command(text)

            # append author and channel information
            c.user = message.author
            c.text_channel = message.channel
            voice_state = message.author.voice
            c.voice_channel = None if not voice_state else voice_state.channel
            c.guild = message.guild
            
            # execute command
            await self.callback(c)

    # parses the ./mictest commands and returns a Command object
    def parse_command(self, text: str) -> Command:
        cmd = Command()

        commandIdx = text.find('./mictest')
        if commandIdx == 0:

            if len(text) >= 9:
                options = remove_white_spaces(text[9:])

                if len(options) > 2:
                    options = options.split(" ")

                    for option in options:
                        if option[0:2] == "--" and len(option) > 2:
                            option_text = option[2:]
                            
                            if option_text == 'help':
                                cmd.help = True
                                break
                            elif option_text == 'log':
                                cmd.log = True
                            elif option_text == 'echo':
                                cmd.echo = True
                            elif option_text == 'file':
                                cmd.file = True
                            elif len(option_text) > len('time=') and option_text[0:5] == 'time=':
                                cmd.duration = int(option_text[5:])
                        else:
                            print("Not a valid option\n")
                else:
                    print("no options")
            else:
                print("no options")
        else:
            print("keyword not found")

        return cmd