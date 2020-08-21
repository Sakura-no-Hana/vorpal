import os

from discord.ext import commands
from utils.embed import RestrictedEmbed

client = commands.Bot(command_prefix='|')
toggles = dict()  # TODO: put this in a db


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.command()
async def configure(ctx: commands.Context):
    print('hello')
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction('💢')
            return await RestrictedEmbed(ctx).fail(
                'Configuration Failed',
                'Manage Guild permissions are required for configuration.')
    if len(ctx.message.attachments) == 0:
        await ctx.message.add_reaction('💢')
        return await RestrictedEmbed(ctx).fail(
            'Configuration Failed',
            'Please attach a Vorpal config file in order to configure the bot. '
            'See the documentation for more information.')
    # TODO: add in logic for detecting syntax errors
    if ctx.guild:
        await ctx.message.attachments[0].save(f'../data/g{ctx.guild.id}.vorpal')
        if not f'g{ctx.guild.id}' in toggles:
            toggles[f'g{ctx.guild.id}'] = True
    else:
        await ctx.message.attachments[0].save(f'../data/u{ctx.author.id}.vorpal')
        if not f'u{ctx.author.id}' in toggles:
            toggles[f'u{ctx.author.id}'] = True

    await ctx.message.add_reaction('✅')
    await RestrictedEmbed(ctx).unfail('Configuration Passed', 'File saved.')


@client.command()
async def toggle(ctx: commands.Context):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction('💢')
            return await RestrictedEmbed(ctx).fail(
                'Toggle Failed',
                'Manage Guild permissions are required to toggle.')
        if not f'g{ctx.guild.id}' in toggles:
            toggles[f'g{ctx.guild.id}'] = True
        toggles[f'g{ctx.guild.id}'] = not toggles[f'g{ctx.guild.id}']
        await ctx.message.add_reaction('✅')
        await RestrictedEmbed(ctx).unfail(
            'Toggle Succeeded',
            'The bot will now {}follow custom commands.'.format(
                '' if toggles[f'g{ctx.guild.id}'] else 'not '))
    else:
        if not f'u{ctx.author.id}' in toggles:
            toggles[f'u{ctx.author.id}'] = True
        toggles[f'u{ctx.author.id}'] = not toggles[f'u{ctx.author.id}']
        await ctx.message.add_reaction('✅')
        await RestrictedEmbed(ctx).unfail(
            'Toggle Succeeded',
            'The bot will now {}follow custom commands.'.format(
                '' if toggles[f'u{ctx.author.id}'] else 'not '))


if __name__ == '__main__':
    token = os.environ.get('TOKEN')
    client.run(token)
    print('hello')
