from discord.ext import commands
import discord
import psutil
import os
import config


class misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.accountedStarMessages = []

    @commands.command()
    @commands.is_owner()
    async def purge(self, ctx, num: int):
        if ctx.message.author != self.bot.user:
            await ctx.message.delete()
            await ctx.channel.purge(limit=num)

    @commands.command()
    @commands.is_owner()
    async def send(self, ctx, id: int, *, message):
        x = self.bot.get_channel(id)
        embed = discord.Embed(color=0xff0000)
        embed.description = message
        await x.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, id: int, *, message):
        await self.bot.wait_until_ready()
        x = await self.bot.fetch_user(id)
        embed = discord.Embed(color=0xff0000)
        embed.description = message
        await x.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def ask(self, ctx):
        await self.bot.wait_until_ready()
        members = ctx.guild.members
        for member in members:
            for role in member.roles:
                if (role.name == 'NBTHS') and (member.id not in config.alert_list):
                    x = await self.bot.fetch_user(member.id)
                    embed = discord.Embed(color=0xff0000)
                    embed.description = 'You go to NBTHS, but do not receive scheduling alerts. If you would like ' \
                                        'me to DM you when your classes start and stop, please DM the bot owner'
                    await x.send(embed=embed)
                    break

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id not in self.accountedStarMessages:
            channel = self.bot.get_channel(payload.channel_id)
            orig = await channel.fetch_message(payload.message_id)
            for reaction in orig.reactions:
                if reaction.emoji == '⭐':
                    x = self.bot.get_channel(838440896230981632)
                    if reaction.count >= 5:
                        if payload.channel_id != config.daily_poll_channel_id:
                            embed = discord.Embed(title='\u200b', description=orig.clean_content, color=0x36393F)
                            embed.set_author(name=f'{orig.author.name}', icon_url=orig.author.avatar_url)
                            embed.add_field(name='\u200b', value=f'[jump to message]({orig.jump_url})', inline=False)
                            if orig.attachments:
                                embed.set_image(url=orig.attachments[0].url)
                            await x.send(embed=embed)
                            self.accountedStarMessages.append(payload.message_id)

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
            await ctx.send(f'Cog reloaded')
        except Exception as e:
            await ctx.send(f'Cog could not be reloaded: {e}')

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        try:
            self.bot.load_extension(cog)
            await ctx.send(f'Cog loaded')
        except Exception as e:
            await ctx.send(f'Cog could not be loaded: {e}')

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        try:
            self.bot.unload_extension(cog)
            await ctx.send(f'Cog unloaded')
        except Exception as e:
            await ctx.send(f'Cog could not be unloaded: {e}')

    @commands.command(aliases=["info", "stats", "status"])
    async def about(self, ctx):
        ramUsage = psutil.Process(os.getpid()).memory_full_info().rss / 1024**2
        avgmembers = sum(g.member_count for g in self.bot.guilds) / len(self.bot.guilds)

        embedColour = discord.Embed.Empty
        if hasattr(ctx, "guild") and ctx.guild is not None:
            embedColour = ctx.me.top_role.colour

        embed = discord.Embed(colour=embedColour)
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        embed.add_field(name=f"Developer", value="TekRekon", inline=True)
        embed.add_field(name="Library", value="discord.py", inline=True)
        embed.add_field(name="Servers", value=f"{len(ctx.bot.guilds)} ( avg: {avgmembers:,.2f} users/server )", inline=True)
        embed.add_field(name="Commands loaded", value=f'{len([x.name for x in self.bot.commands])}', inline=True)
        embed.add_field(name="RAM", value=f"{ramUsage:.2f} MB", inline=True)

        await ctx.send(content=f"ℹ About **{ctx.bot.user}** | **Version 1.1**", embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def propose(self, ctx, *, message):
        if ctx.author.id not in [43543, 4355]:
            x = self.bot.get_channel(config.suggestions_channel_id)
            embed = discord.Embed(title=message, color=0x36393F)
            embed.set_author(name=f'{ctx.author.name}', icon_url=ctx.author.avatar_url)
            sent_embed = await x.send(embed=embed)
            await sent_embed.add_reaction('⏬')
            await sent_embed.add_reaction('⬇️')
            await sent_embed.add_reaction('⬆️')
            await sent_embed.add_reaction('⏫')

    @commands.command()
    @commands.is_owner()
    async def decide(self, ctx, msgID, decision, *, reason):
        await ctx.message.delete()
        print(msgID)
        x = await ctx.fetch_message(msgID)
        old_embed = x.embeds[0]
        old_embed.add_field(name=f'​{decision}', value=f'{reason}')
        if decision == 'implemented':
            old_embed.colour = 0x00c724
        elif decision == 'inProgress':
            old_embed.colour = 0xffe72e
        elif decision == 'denied':
            old_embed.colour = 0xc70000
        await x.edit(embed=old_embed)

    @commands.command()
    async def lastten(self, ctx, users_id: int):
        oldestMessages = []
        for channel in ctx.guild.text_channels:
            messages = await channel.history(limit=100).flatten()
            for fetchMessage in messages:
                if fetchMessage.author.id != users_id:
                    continue
                if len(oldestMessages) == 0:
                    oldestMessages.append(fetchMessage)
                elif fetchMessage not in oldestMessages:
                    for i, x in enumerate(oldestMessages):
                        if fetchMessage.created_at > x.created_at:
                            oldestMessages.insert(i, fetchMessage)
                            break
                    oldestMessages.append(fetchMessage)
        if len(oldestMessages) != 0:
            print([x.content for x in oldestMessages])
            await ctx.send(f"Previous messages found by user {users_id}:")
            i = 0
            while i < 10:
                if oldestMessages[i]:
                    await ctx.send(f"{i+1}: **{oldestMessages[i].content}** at {oldestMessages[i].created_at} "
                                   f"in channel {oldestMessages[i].channel.name}")
                i += 1
        else:
            await ctx.send("No messages found :/")


def setup(bot):
    bot.add_cog(misc(bot))