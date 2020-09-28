import json
from pathlib import Path
import os
import zlib

import discord
from discord.ext import commands
import lark
import pymongo

from utils.embed import RestrictedEmbed
from utils.lang.lex import parse

client = commands.Bot(command_prefix="|", help_command=None)
client._websocketbuffer = bytearray()
client._zlib = zlib.decompressobj()
client._tempid = ""
client.botrole = dict()
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["vorpal"]
toggles = mydb["toggles"]
guilds = dict()


@client.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.listening, name=" your configuration"
    )
    await client.change_presence(status=discord.Status.idle, activity=activity)
    print("We have logged in as {0.user}".format(client))


@client.event
async def on_socket_raw_receive(msg):
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
        for role in msg["d"]["roles"]:
            if "tags" in role:
                if "bot_id" in role["tags"]:
                    if (
                            role["tags"]["bot_id"] == client._tempid
                    ):  # check if it's equal to the bot id
                        client.botrole[msg["d"]["id"]] = role["id"]
    elif msg["t"] == "READY":
        client._tempid = msg["d"]["user"]["id"]
    # print(msg)


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

    await msg.add_reaction("💢")
    await RestrictedEmbed(await client.get_context(msg)).send(
        "Verification Failed",
        "Please set the color of Vorpal's role, "
        f"<@&{client.botrole[str(msg.guild.id)]}>, to #2f3136.",
    )


@client.command()
async def configure(ctx: commands.Context):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction("💢")
            return await RestrictedEmbed(ctx).send(
                "Configuration Failed",
                "Manage Guild permissions are required for configuration.",
            )
    if len(ctx.message.attachments) == 0:
        await ctx.message.add_reaction("💢")
        return await RestrictedEmbed(ctx).send(
            "Configuration Failed",
            "Please attach a Vorpal config file in order to configure the bot. "
            "See the documentation for more information.",
        )
    if ctx.guild:
        await ctx.message.attachments[0].save(
            path := Path(f"../data/u{ctx.author.id}.vorpal")
        )
        if toggles.find_one({"id": f"g{ctx.guild.id}"}) is not None:
            toggles.insert_one({"id": f"g{ctx.guild.id}", "toggle": True})
    else:
        await ctx.message.attachments[0].save(
            path := Path(f"../data/u{ctx.author.id}.vorpal")
        )
        if toggles.find_one({"id": f"u{ctx.author.id}"}) is not None:
            toggles.insert_one({"id": f"u{ctx.author.id}", "toggle": True})
    try:
        # TODO: actually save the tree in memory
        parse(path)
    except lark.exceptions.LarkError:
        path.unlink()
        await ctx.message.add_reaction("💢")
        return await RestrictedEmbed(ctx).send(
            "Configuration Failed",
            "The Vorpal config file was improperly formatted. "
            "See the documentation for more information.",
        )

    await ctx.message.add_reaction("✅")
    await RestrictedEmbed(ctx).send("Configuration Passed", "File saved.")


@client.command()
async def toggle(ctx: commands.Context):
    if ctx.guild:
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            await ctx.message.add_reaction("💢")
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
        await ctx.message.add_reaction("✅")
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
        await ctx.message.add_reaction("✅")
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
