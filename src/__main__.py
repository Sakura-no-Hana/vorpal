import datetime
import json
from pathlib import Path
import os
import re
import uuid
import zlib

import discord
from discord.ext import commands
import humanize
import lark
import pymongo
import requests

from utils.embed import RestrictedEmbed
from utils.lang.lex import parse
from utils.code import CodeConverter, LinkedFileTooLarge, CodeNotFound

client = commands.Bot(command_prefix="|", help_command=None)
client._websocketbuffer = bytearray()
client._zlib = zlib.decompressobj()
client.botrole = dict()
client.react = ("💯", "💢")
client.reurl = re.compile(
    r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))'
)
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
    if type(msg) is bytes:
        client._websocketbuffer.extend(msg)

        if len(msg) >= 4:
            if msg[-4:] == b"\x00\x00\xff\xff":
                msg = client._zlib.decompress(client._websocketbuffer)
                msg = msg.decode("utf-8")
                client._websocketbuffer = bytearray()
            else:
                return
        else:
            return

    msg = json.loads(msg)

    if msg["t"] == "GUILD_CREATE":
        # custom event used to find bot integration role since dpy doesn't support role tags
        client.dispatch("guild_create", msg["d"])
    # print(msg)


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
        return await client.process_commands(msg)

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
    if ctx.guild:
        if toggles.find_one({"id": f"g{ctx.guild.id}"}) is not None:
            toggles.insert_one({"id": f"g{ctx.guild.id}", "toggle": True})
    else:
        if toggles.find_one({"id": f"u{ctx.author.id}"}) is not None:
            toggles.insert_one({"id": f"u{ctx.author.id}", "toggle": True})

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
    # TODO: make all of this stuff work in mongo
    if os.path.exists(Path(f"../data/{name}.vorpal")):
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
        if (value := toggles.find_one({"id": f"g{ctx.guild.id}"})) is not None:
            toggles.replace_one(
                {"id": f"g{ctx.guild.id}"},
                {"id": f"g{ctx.guild.id}", "toggle": not value["toggle"]},
            )
        else:
            toggles.insert_one(value := {"id": f"g{ctx.guild.id}", "toggle": False})
        await ctx.message.add_reaction(client.react[0])
        await RestrictedEmbed(ctx).send(
            "Toggle Succeeded",
            "The bot will now {}follow custom commands.".format(
                "" if value["toggle"] else "not "
            ),
        )
    else:
        if (value := toggles.find_one({"id": f"u{ctx.author.id}"})) is not None:
            toggles.replace_one(
                {"id": f"u{ctx.author.id}"},
                {"id": f"u{ctx.author.id}", "toggle": not value["toggle"]},
            )
        else:
            toggles.insert_one(value := {"id": f"u{ctx.author.id}", "toggle": False})
        await ctx.message.add_reaction(client.react[0])
        await RestrictedEmbed(ctx).send(
            "Toggle Succeeded",
            "The bot will now {}follow custom commands.".format(
                "" if value["toggle"] else "not "
            ),
        )


@client.command()
async def help(ctx: commands.Context):
    await RestrictedEmbed(ctx).field(
        "|configure [config:file]",
        "Configure the bot using the attached file, `config`. By default, this is restricted to those with the Manage Guild permission. See file syntax in the bot's documentation.",
    ).field(
        "|toggle",
        "Toggle whether the bot uses the config file. This is so reckless users have a killswitch.",
    ).field(
        "|help", "Shows this command."
    ).send(
        "Help", "|command name [var name:var type] <optional var name:var type>"
    )


if __name__ == "__main__":
    token = os.environ.get("TOKEN")
    client.run(token)
