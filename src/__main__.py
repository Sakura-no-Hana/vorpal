import os

from discord.ext import commands
from yaml import safe_load

from utils.embed import RestrictedEmbed

client = commands.Bot(command_prefix='!')

events = {'typing', 'message', 'message_delete', 'bulk_message_delete', 'message_edit',
          'reaction_add', 'reaction_remove', 'channel_create', 'channel_delete', 'channel_update',
          'pin_update', 'integrations_update', 'webhooks_update', 'member_join', 'member_leave',
          'member_update', 'guild_update', 'role_create', 'role_delete', 'role_update',
          'emoji_update', 'voice_state_update', 'member_ban', 'member_unban', 'invite_create',
          'invite_delete'}


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
            'Please attach a YAML file in order to configure the bot. '
            'See the documentation for more information.')
    # TODO: add in logic for detecting syntax errors
    if ctx.guild:
        await ctx.message.attachments[0].save(f'../data/g{ctx.guild.id}.vorpal')
    else:
        await ctx.message.attachments[0].save(f'../data/u{ctx.author.id}.vorpal')

    if ctx.guild:
        with open(f'../data/g{ctx.guild.id}.vorpal', 'r') as f:
            temp = safe_load(f)
    else:
        with open(f'../data/u{ctx.author.id}.vorpal', 'r') as f:
            temp = safe_load(f)

    if not all(event in temp for event in events):
        await ctx.message.add_reaction('💢')
        return await RestrictedEmbed(ctx).fail(
            'This YAML file does not match the format specified in the documentation. '
            'See the documentation for more information.')

    await ctx.message.add_reaction('✅')
    await RestrictedEmbed(ctx).unfail('File saved.')


token = os.environ.get('TOKEN')
client.run(token)
