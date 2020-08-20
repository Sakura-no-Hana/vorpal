import os

from discord.ext import commands
from utils.embed import RestrictedEmbed

client = commands.Bot(command_prefix='|')

@client.command()
async def configure(ctx: commands.Context):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction('💢')
            return await RestrictedEmbed(ctx).fail(
                'Manage Guild permissions are required for configuration.')
    if len(ctx.message.attachments) == 0:
        await ctx.message.add_reaction('💢')
        return await RestrictedEmbed(ctx).fail(
            'Please attach a Vorpal config file in order to configure the bot. '
            'See the documentation for more information.')
    # TODO: add in logic for detecting syntax errors
    if ctx.guild:
        await ctx.message.attachments[0].save(f'../data/g{ctx.guild.id}.vorpal')
    else:
        await ctx.message.attachments[0].save(f'../data/u{ctx.author.id}.vorpal')

    await ctx.message.add_reaction('✅')
    await RestrictedEmbed(ctx).unfail('File saved.')


token = os.environ.get('TOKEN')
client.run(token)
