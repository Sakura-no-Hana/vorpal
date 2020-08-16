import os

from discord.ext import commands
import requests

client = commands.Bot(command_prefix='!')


@client.command()
async def configure(ctx):
    attachment_url = ctx.message.attachments[0].url
    file_request = requests.get(attachment_url)
    with open(f'../data/{ctx.guild.id}.vorpal', 'w+') as f:
        f.write(file_request.content.decode("utf-8"))


token = os.environ.get('TOKEN')
client.run(token)
