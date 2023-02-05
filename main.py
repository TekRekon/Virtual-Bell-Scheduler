from discord.ext import commands
import discord
import logging
import config

logging.basicConfig(level=logging.INFO)

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='.', help_command=None, intents=intents)

@bot.event
async def on_ready():
    print('Rigged for silent running')

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def help(ctx):

    embed = discord.Embed(color=0x2596be)
    embed.set_author(name='Help Menu', icon_url='https://cdn.discordapp.com/attachments/488700267060133889/694687205469323284/settingjif.gif')
    embed.description = '`<>` = required argument \n `[]` = optional argument \n `.` = bot prefix'
    embed.add_field(name='​\n Scheduling', value=f'`.day` \n > Tells you today\'s day (automatically updated ~30 minutes before school) \n \n `.type` \n > Tells you today\'s schedule (normal, extended, early) \n \n `.schedule` \n > Gives you a copy of the schedule \n \n `.working` \n > Tells you if scheduling messages are currently being sent \n \n `.time` \n > Returns the time left until the next alert \n \n `.glitch` \n > Returns a random glitch', inline=False)
    embed.add_field(name='​\n Admin', value='`.setDay <0/1/2/3/4>` \n > Override the current day \n \n `.setType <normal/early/extended/testing>` \n > Override the current schedule \n \n `.purge <numMessages>` \n > Delete a specified number of messages in a channel \n \n `.decide <msgID> <implemented/inProgress/denied> <reason>` \n > Deny or approve server suggestions. Use in the same channel as the server suggestions \n \n `.cogs` \n > Returns a list of cog names and loading commands')

    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def cogs(ctx):
    embed = discord.Embed(color=0x2596be)
    embed.set_author(name='Cogs', icon_url='https://cdn.discordapp.com/attachments/488700267060133889/'
                                           '694687205469323284/settingjif.gif')
    embed.description = '`.reload`|`.unload`|`.reload` \n misc \n Scheduler \n DailyPoll \n CarouselStatus'
    await ctx.send(embed=embed)

bot.load_extension('misc')
print("misc initiated")

bot.load_extension('CarouselStatus')
print("CarouselStatus initiated")

bot.load_extension('Scheduler')
print("Scheduler initiated")

bot.load_extension('DailyPoll')
print("DailyPoll initiated")


bot.run(config.bot_token)

