import discord
import asyncio
from threading import Thread
import string


class Plugin:
    name = 'discord bridge'
    author = 'NikZapp'
    config = {'bot_motd': '',
              'bot_token': '',
              'bot_channel': 0}
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    client = discord.Client(activity=discord.Game(name=config['bot_motd']), intents=intents)
    event_dict_init = {}
    channel = None

    def setup(event_dict):
        Plugin.event_dict_init = event_dict.copy()
        loop = asyncio.get_event_loop()
        loop.create_task(Plugin.client.start(Plugin.config['bot_token']))
        Thread(target=loop.run_forever).start()

    async def on_discord(event_dict):
        for i in event_dict['message'].content:
            if i not in string.printable[:-5]:
                embed = discord.Embed(title="Invalid character!", color=0xf9330e)
                embed.set_footer(text=f'Unable to send `{i}`')
                await event_dict['message'].channel.send(embed=embed)
                return
        Plugin.event_dict_init['amethyst']['plugins']['mcpi_chat'].send(f'[{str(event_dict["message"].author)[:-5]}] {event_dict["message"].content}')

    async def on_chat(event_dict):
        await Plugin.channel.send(f'{event_dict["username"]}: {event_dict["message"]}')

    async def on_join(event_dict):
        await Plugin.channel.send(f'''
```diff
+ {event_dict['username']}
```''')

    async def on_leave(event_dict):
        await Plugin.channel.send(f'''
```diff
- {event_dict['username']}
```''')

    async def on_death(event_dict):
        await Plugin.channel.send(f'''
```fix
{event_dict['username']} died
```''')

    @client.event
    async def on_ready():
        print(f'Bot online as')
        print(f'{Plugin.client.user.name}')
        print(f'{Plugin.client.user.id}')
        Plugin.channel = Plugin.client.get_channel(Plugin.config['bot_channel'])

    @client.event
    async def on_message(discord_message):
        if discord_message.channel.id == Plugin.config['bot_channel'] and discord_message.author != Plugin.client.user:
            event_dict = {'message': discord_message}
            await Plugin.on_discord(event_dict)

    events = {'amethyst': {
                  'setup': setup},
              'mcpi_chat': {
                  'chat': on_chat,
                  'death': on_death,
                  'join': on_join,
                  'leave': on_leave}}
