import discord


class RestrictedEmbed:
    color = discord.Color(0x2F3136)

    def __init__(self, ctx):
        self.ctx = ctx
        self.fields = []

    async def send(self, title: str = "Operation Succeeded", description: str = ""):
        if self.ctx.guild:
            if not self.ctx.channel.permissions_for(self.ctx.guild.me).embed_links:
                msg = f"**{title}**\n{description}"
                for field in self.fields:
                    msg += f"\n\n`{field[0]}`\n{field[1]}"
                return await self.ctx.send(msg)
        embed = discord.Embed(
            title=title, color=RestrictedEmbed.color, description=description
        )
        if self.ctx.guild:
            embed.set_author(name=self.ctx.guild.name, icon_url=self.ctx.guild.icon_url)
        else:
            embed.set_author(
                name=self.ctx.author.name + "#" + self.ctx.author.discriminator,
                icon_url=self.ctx.author.avatar_url,
            )
        embed.set_footer(
            text=self.ctx.author.display_name, icon_url=self.ctx.author.avatar_url
        )
        embed.set_thumbnail(url=self.ctx.bot.user.avatar_url)
        for field in self.fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
        await self.ctx.send(embed=embed)
        # file = discord.File('../res/swordspinr.gif', filename='vorpal.gif')
        # embed.set_thumbnail(url='attachment://vorpal.gif')
        # await self.ctx.send(file=file, embed=embed)

    def field(self, name: str, value: str, inline: bool = False):
        self.fields.append((name, value, inline))
        return self
