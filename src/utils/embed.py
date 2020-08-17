import discord


class RestrictedEmbed:
    def __init__(self, ctx):
        self.ctx = ctx

    async def fail(self, description=''):
        if self.ctx.guild:
            if not self.ctx.channel.permissions_for(self.ctx.guild.me).embed_links:
                return await self.ctx.send(f'**Configuration Failed**\n{description}')
        embed = discord.Embed(title='Configuration Failed')
        if self.ctx.guild:
            embed.set_author(name=self.ctx.guild.name, icon_url=self.ctx.guild.icon_url)
            embed.color = self.ctx.guild.me.color
        else:
            embed.set_author(name=self.ctx.author.name + '#' + self.ctx.author.discriminator,
                             icon_url=self.ctx.author.avatar_url)
        embed.set_footer(text=self.ctx.author.display_name, icon_url=self.ctx.author.avatar_url)
        embed.set_thumbnail(url=self.ctx.bot.user.avatar_url)
        embed.description = description
        await self.ctx.send(embed=embed)

    async def unfail(self, description=''):
        if self.ctx.guild:
            if not self.ctx.channel.permissions_for(self.ctx.guild.me).embed_links:
                return await self.ctx.send(f'**Configuration Passed**\n{description}')
        embed = discord.Embed(title='Configuration Passed')
        if self.ctx.guild:
            embed.set_author(name=self.ctx.guild.name, icon_url=self.ctx.guild.icon_url)
            embed.color = self.ctx.guild.me.color
        else:
            embed.set_author(name=self.ctx.author.name + '#' + self.ctx.author.discriminator,
                             icon_url=self.ctx.author.avatar_url)
        embed.set_footer(text=self.ctx.author.display_name, icon_url=self.ctx.author.avatar_url)
        embed.set_thumbnail(url=self.ctx.bot.user.avatar_url)
        embed.description = description
        await self.ctx.send(embed=embed)
