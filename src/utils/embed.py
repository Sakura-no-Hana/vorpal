import discord


class RestrictedEmbed:
    def __init__(self, ctx):
        self.ctx = ctx

    async def send(self, title: str = 'Operation Succeeded', description: str = ''):
        if self.ctx.guild:
            if not self.ctx.channel.permissions_for(self.ctx.guild.me).embed_links:
                return await self.ctx.send(f'**{title}**\n{description}')
        embed = discord.Embed(title=title, color=self.ctx.guild.me.color, description=description)
        if self.ctx.guild:
            embed.set_author(name=self.ctx.guild.name, icon_url=self.ctx.guild.icon_url)
        else:
            embed.set_author(name=self.ctx.author.name + '#' + self.ctx.author.discriminator,
                             icon_url=self.ctx.author.avatar_url)
        embed.set_footer(text=self.ctx.author.display_name, icon_url=self.ctx.author.avatar_url)
        embed.set_thumbnail(url=self.ctx.bot.user.avatar_url)
        file = discord.File('../res/swordspinr.gif', filename='vorpal.gif')
        embed.set_thumbnail(url='attachment://vorpal.gif')
        await self.ctx.send(file=file, embed=embed)
