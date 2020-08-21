import os

import pymongo
from discord.ext import commands
from utils.embed import RestrictedEmbed

client = commands.Bot(command_prefix='|')
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["vorpal"]
toggles = mydb["toggles"]


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.command()
async def configure(ctx: commands.Context):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction('💢')
            return await RestrictedEmbed(ctx).send(
                'Configuration Failed',
                'Manage Guild permissions are required for configuration.')
    if len(ctx.message.attachments) == 0:
        await ctx.message.add_reaction('💢')
        return await RestrictedEmbed(ctx).send(
            'Configuration Failed',
            'Please attach a Vorpal config file in order to configure the bot. '
            'See the documentation for more information.')
    # TODO: add in logic for detecting syntax errors
    if ctx.guild:
        await ctx.message.attachments[0].save(f'../data/g{ctx.guild.id}.vorpal')
        if toggles.find_one({'id': f'g{ctx.guild.id}'}) is not None:
            toggles.insert_one({'id': f'g{ctx.guild.id}', 'toggle': True})
    else:
        await ctx.message.attachments[0].save(f'../data/u{ctx.author.id}.vorpal')
        if toggles.find_one({'id': f'u{ctx.author.id}'}) is not None:
            toggles.insert_one({'id': f'u{ctx.author.id}', 'toggle': True})

    await ctx.message.add_reaction('✅')
    await RestrictedEmbed(ctx).send('Configuration Passed', 'File saved.')


@client.command()
async def toggle(ctx: commands.Context):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction('💢')
            return await RestrictedEmbed(ctx).send(
                'Toggle Failed',
                'Manage Guild permissions are required to toggle.')
        if (value := toggles.find_one({'id': f'g{ctx.guild.id}'})) is not None:
            toggles.replace_one({'id': f'g{ctx.guild.id}'},
                                {'id': f'g{ctx.guild.id}',
                                 'toggle': not value['toggle']})
        else:
            toggles.insert_one((value := {'id': f'g{ctx.guild.id}', 'toggle': False}))
        await ctx.message.add_reaction('✅')
        await RestrictedEmbed(ctx).send(
            'Toggle Succeeded',
            'The bot will now {}follow custom commands.'.format(
                '' if value['toggle'] else 'not '))
    else:
        if (value := toggles.find_one({'id': f'u{ctx.author.id}'})) is not None:
            toggles.replace_one({'id': f'u{ctx.author.id}'},
                                {'id': f'u{ctx.author.id}',
                                 'toggle': not value['toggle']})
        else:
            toggles.insert_one((value := {'id': f'u{ctx.author.id}', 'toggle': False}))
        await ctx.message.add_reaction('✅')
        await RestrictedEmbed(ctx).send(
            'Toggle Succeeded',
            'The bot will now {}follow custom commands.'.format(
                '' if value['toggle'] else 'not '))


if __name__ == '__main__':
    token = os.environ.get('TOKEN')
    client.run(token)
