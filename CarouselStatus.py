from discord.ext import commands, tasks
import discord
import Scheduler
import psycopg2
import asyncio
import config


class CarouselStatus(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.con = psycopg2.connect(config.database_url)

    async def day(self):
        cur = self.con.cursor()
        cur.execute("SELECT day FROM info WHERE id = 1")
        day = cur.fetchall()[0][0]
        return day

    async def school_type(self):
        cur = self.con.cursor()
        cur.execute("SELECT type FROM info WHERE id = 1")
        type = cur.fetchall()[0][0]
        return type

    @commands.Cog.listener()
    async def on_ready(self):
        self.carousel_status.start()

    @tasks.loop(seconds=10.0)
    async def carousel_status(self):
        schoolType = await CarouselStatus.school_type(self)
        day = await CarouselStatus.day(self)
        schedule = Scheduler.getSchedule(schoolType, day)
        timeLeft = 0
        for elem in schedule:
            time = Scheduler.get_wait_time(elem[0])
            if time == 0:
                continue
            else:
                timeLeft = time
                break

        if timeLeft == 0:
            msg = 'Alerts are not being sent'
        elif timeLeft/60 < 1:
            msg = f'{timeLeft} sec>next alert'
        else:
            minutes, remainder = divmod(timeLeft, 60)
            seconds = int(round(remainder/100*60, 0))
            msg = f'{minutes} min, {seconds} sec>next alert'

        await asyncio.sleep(10)
        await self.bot.change_presence(activity=discord.Game(f'Schedule: {schoolType}'))
        await asyncio.sleep(10)
        await self.bot.change_presence(activity=discord.Game(msg))
        await asyncio.sleep(10)
        await self.bot.change_presence(activity=discord.Game(f'Day: {day}'))
        await asyncio.sleep(10)
        await self.bot.change_presence(activity=discord.Game(f'Latency: {round(self.bot.latency*1000, 2)}ms'))


def setup(bot):
    bot.add_cog(CarouselStatus(bot))
