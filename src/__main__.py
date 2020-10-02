import datetime
from pathlib import Path
import os
import uuid

import discord
from discord.ext import commands
import humanize
import lark
import pymongo
from sqlitedict import SqliteDict

from utils.embed import RestrictedEmbed
from utils.lang.lex import parse
from utils.code import CodeConverter, LinkedFileTooLarge, CodeNotFound
from utils.socket import Decoder

client = commands.Bot(command_prefix="|", help_command=None)
client.botrole = dict()
client.raw = Decoder()
client.react = ("💯", "💢")
client.toggles = SqliteDict(filename=Path("../data/toggle.db"), autocommit=True)
client.loads = SqliteDict(filename=Path("../data/load.db"), autocommit=True)
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["vorpal"]
toggles = mydb["toggles"]
loads = mydb["loads"]


@client.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.listening, name=" your configuration"
    )
    await client.change_presence(status=discord.Status.idle, activity=activity)
    print("We have logged in as {0.user}".format(client))


@client.event
async def on_socket_raw_send(data):
    # this is for debugging purposes
    print(data)


@client.event
async def on_socket_raw_receive(msg):
    # TODO: actually have events work with uploaded code
    msg = client.raw.decode(msg)

    if "t" in msg:
        if msg["t"] == "GUILD_CREATE":
            # custom event used to find bot integration role since dpy doesn't support role tags
            client.dispatch("guild_create", msg["d"])


@client.event
async def on_guild_create(msg: dict):
    for role in msg["roles"]:
        if "tags" in role:
            if "bot_id" in role["tags"]:
                if role["tags"]["bot_id"] == str(
                        client.user.id
                ):  # check if it's equal to the bot id
                    client.botrole[msg["id"]] = role["id"]
                    # print(msg["id"])
                    print(msg["roles"])
                    return


@client.event
async def on_message(msg: discord.Message):
    if not msg.guild:
        if f"u{msg.author.id}" not in client.toggles:
            client.toggles[f"u{msg.author.id}"] = True
        if f"u{msg.author.id}" not in client.loads:
            client.loads[f"u{msg.author.id}"] = set()
        return await client.process_commands(msg)

    if f"g{msg.guild.id}" not in client.toggles:
        client.toggles[f"g{msg.guild.id}"] = True
    if f"g{msg.guild.id}" not in client.loads:
        client.loads[f"g{msg.guild.id}"] = set()

    for role in msg.guild.me.roles:
        if str(role.id) in client.botrole[str(msg.guild.id)]:
            r = role
            break

    if r.color == discord.Color(0x2F3136):
        return await client.process_commands(msg)

    if msg.content[0] != "|":
        return

    await msg.add_reaction(client.react[1])
    await RestrictedEmbed(await client.get_context(msg)).send(
        "Verification Failed",
        "Please set the color of Vorpal's role, "
        f"<@&{client.botrole[str(msg.guild.id)]}>, to #2f3136.",
    )


@client.command()
@commands.cooldown(5, 86400, commands.BucketType.user)
async def upload(ctx: commands.Context, *, msg: CodeConverter = None):
    name = uuid.uuid4()
    if not msg:
        msg = await CodeConverter.convert(ctx, "")
    with open(path := Path(f"../data/{name}.vorpal"), "w+") as file:
        file.write(msg)

    try:
        parse(path)
    except lark.exceptions.LarkError:
        path.unlink()
        await ctx.message.add_reaction(client.react[1])
        return await RestrictedEmbed(ctx).send(
            "Configuration Failed",
            "The Vorpal config file was improperly formatted. "
            "See the documentation for more information.",
        )

    await ctx.message.add_reaction(client.react[0])
    await RestrictedEmbed(ctx).send(
        "Upload Passed",
        f"File saved as `{name}`. Please record this ID. You must load this file in with ```|load {name}``` for it to work.",
    )


@upload.error
async def upload_error(ctx: commands.Context, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
        retry = humanize.naturaldelta(datetime.timedelta(seconds=error.retry_after))
        await ctx.message.add_reaction(client.react[1])
        await RestrictedEmbed(ctx).send(
            "Upload Failed",
            "You have invoked the upload command too many times in a relatively short period of time. "
            f"The limit is 5 uploads per day. Please try again in {retry}.",
        )
    elif isinstance(error, LinkedFileTooLarge):
        await ctx.message.add_reaction(client.react[1])
        await RestrictedEmbed(ctx).send(
            "Upload Failed",
            "The file retrieved from that URL is too large. "
            "The largest allowable file size from a URL is 50 megabytes.",
        )
    elif isinstance(error, CodeNotFound):
        await ctx.message.add_reaction(client.react[1])
        await RestrictedEmbed(ctx).send(
            "Upload Failed",
            "Your message contained no code to upload. "
            "Please either upload a file, use a URL, or put your code in code blocks.",
        )
    else:
        raise error


@client.command()
async def load(ctx: commands.Context, name: str):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction(client.react[1])
            return await RestrictedEmbed(ctx).send(
                "Loading Failed",
                "Manage Guild permissions are required for configuration.",
            )
    if os.path.exists(Path(f"../data/{name}.vorpal")):
        if ctx.guild:
            client.loads[f"g{ctx.guild.id}"].add(name)
        else:
            client.loads[f"u{ctx.author.id}"].add(name)
        await ctx.message.add_reaction(client.react[0])
        await RestrictedEmbed(ctx).send(
            "Load Succeeded",
            f"Module `{name}` loaded. To unload, please use:```|unload {name}```",
        )
    else:
        await ctx.message.add_reaction(client.react[1])
        await RestrictedEmbed(ctx).send(
            "Load Failed",
            f"Module `{name}` not found.",
        )


@client.command()
async def unload(ctx: commands.Context, name: str):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction(client.react[1])
            return await RestrictedEmbed(ctx).send(
                "Unloading Failed",
                "Manage Guild permissions are required for configuration.",
            )
    try:
        if ctx.guild:
            client.loads[f"g{ctx.guild.id}"].remove(name)
        else:
            client.loads[f"u{ctx.author.id}"].remove(name)
    except ValueError:
        pass
    await ctx.message.add_reaction(client.react[0])
    await RestrictedEmbed(ctx).send(
        "Unload Succeeded",
        f"Module `{name}` unloaded. To unload, please use:```|load {name}```",
    )


@client.command()
async def toggle(ctx: commands.Context):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction(client.react[1])
            return await RestrictedEmbed(ctx).send(
                "Toggle Failed", "Manage Guild permissions are required to toggle."
            )

        client.toggles[f"g{ctx.guild.id}"] = not client.toggles[f"g{ctx.guild.id}"]

        await ctx.message.add_reaction(client.react[0])
        await RestrictedEmbed(ctx).send(
            "Toggle Succeeded",
            "The bot will now {}follow custom commands.".format(
                "" if client.toggles[f"g{ctx.guild.id}"] else "not "
            ),
        )
    else:
        client.toggles[f"u{ctx.author.id}"] = not client.toggles[f"u{ctx.author.id}"]

        await ctx.message.add_reaction(client.react[0])
        await RestrictedEmbed(ctx).send(
            "Toggle Succeeded",
            "The bot will now {}follow custom commands.".format(
                "" if client.toggles[f"u{ctx.author.id}"] else "not "
            ),
        )


# @client.command()
# async def help(ctx: commands.Context):
#     await RestrictedEmbed(ctx).field(
#         "|configure [config:file]",
#         "Configure the bot using the attached file, `config`. By default, this is restricted to those with the Manage Guild permission. See file syntax in the bot's documentation.",
#     ).field(
#         "|toggle",
#         "Toggle whether the bot uses the config file. This is so reckless users have a killswitch.",
#     ).field(
#         "|help", "Shows this command."
#     ).send(
#         "Help", "|command name [var name:var type] <optional var name:var type>"
#     )


if __name__ == "__main__":
    token = os.environ.get("TOKEN")
    client.run(token)
