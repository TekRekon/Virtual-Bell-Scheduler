from discord.ext import commands, tasks
import time
import asyncio
import psycopg2
import datetime
import config
# military: 00:00:00 = new day

class Scheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.con = psycopg2.connect(config.database_url)
        self.alerts.start()
        self.waitingToward = None

    @commands.command()
    async def schedule(self, ctx):
        cur = self.con.cursor()
        cur.execute("SELECT day FROM info WHERE id = 1")
        day = cur.fetchall()[0][0]
        if day == 0:
            await ctx.send('https://media.discordapp.net/attachments/806521612684754995/882459831179542578/'
                           'unknown.png?width=853&height=559')
        else:
            await ctx.send('https://media.discordapp.net/attachments/754012496947314808/881582941057191997/'
                           'unknown.png?width=859&height=559')

    @commands.command()
    async def map(self, ctx):
        await ctx.send('https://media.discordapp.net/attachments/754012496947314808/881928430285905970/'
                       'Document_6.jpg?width=702&height=559')
        await ctx.send('https://media.discordapp.net/attachments/754012496947314808/881928430587904071/'
                       'Document_5.jpg?width=749&height=559')

    @commands.command()
    async def test(self, ctx):
        await ctx.send('10:59 -- period 4 ends now -- 4 minutes until period 5 (11:03) (see below) \n '
                       'Lunch A=11:03-11:33 / Period 5=11:37-12:16 \n OR \n Class=11:03-11:42 / Lunch B=11:46-12:16')

    @commands.command()
    @commands.is_owner()
    async def setType(self, ctx, type: str):
        if type not in ['normal', 'early', 'extended', 'testing', 'delayed', 'pep', 'unknown']:
            await ctx.send('Invalid input, options are normal, early, extended, testing, delayed, pep, unknown')
            return
        cur = self.con.cursor()
        cur.execute(f"UPDATE info SET type = %s WHERE id = 1", (type,))
        self.con.commit()
        await ctx.send(f'Following new schedule: {type}')

    @commands.command()
    @commands.is_owner()
    async def setDay(self, ctx, day: int):
        if day not in [0, 1, 2, 3, 4]:
            await ctx.send('Invalid input')
            return
        cur = self.con.cursor()
        cur.execute("UPDATE info SET day = %s WHERE id = 1", (day,))
        self.con.commit()
        await ctx.send(f'Following new day: {day}')

    @commands.command()
    async def day(self, ctx):
        cur = self.con.cursor()
        cur.execute("SELECT day FROM info WHERE id = 1")
        day = cur.fetchall()[0][0]
        await ctx.send(f'Today is a day {day}')

    @commands.command()
    async def type(self, ctx):
        cur = self.con.cursor()
        cur.execute("SELECT type FROM info WHERE id = 1")
        type = cur.fetchall()[0][0]
        await ctx.send(f'Today is a {type} schedule')

    @commands.command()
    async def time(self, ctx):
        if self.waitingToward == None:
            await ctx.send(f'Alerts are not being sent.')
        else:
            waitTime = Scheduler.get_wait_time(self.waitingToward[0])
            if waitTime/60 < 1:
                await ctx.send(f'{waitTime} seconds --> next alert: **{self.waitingToward[1]}**')
            else:
                minutes, remainder = divmod(waitTime, 60)
                seconds = int(round(remainder/100*60, 0))
                await ctx.send(f'{minutes} minutes, {seconds} seconds --> next alert: **{self.waitingToward[1]}**')

    @commands.command()
    async def working(self, ctx):
        cur = self.con.cursor()
        cur.execute("SELECT working FROM info WHERE id = 1")
        working = cur.fetchall()[0][0]
        if working == 1:
            await ctx.send(f'I am actively sending schedule alerts')
        else:
            await ctx.send(f'I am not sending schedule alerts right now')

    @commands.command()
    @commands.is_owner()
    async def setWorking(self, ctx, state: int):
        if state not in [0, 1]:
            await ctx.send('Invalid input')
            return
        cur = self.con.cursor()
        cur.execute("UPDATE info SET working = %s WHERE id = 1", (state,))
        self.con.commit()
        await ctx.send(f'Working set to state: {state}')

    @staticmethod
    def getSchedule(type, day):
        if type == 'normal':
            return [('07:40:00', '7:40 -- homeroom starts in 5 minutes'),
                    ('07:45:00', '7:45 -- homeroom starts now -- ends 7:49'),
                    ('07:49:00', '7:49 -- homeroom ends now -- 5 minutes until session 1 (7:54)'),
                    ('07:54:00', '7:54 -- session 1 starts now -- ends 8:49'),
                    ('08:49:00', '8:49 -- session 1 ends now -- 5 minutes until session 2 (8:54)'),
                    ('08:54:00', '8:54 -- session 2 starts now -- ends 9:49'),
                    ('09:49:00', '9:49 -- session 2 ends now -- 5 minutes until session 3 (9:54)'),
                    ('09:54:00', '9:54 -- session 3 starts now -- ends 10:49'),
                    ('10:49:00', '10:49 -- **A LUNCH ONLY**: session 3 ends now, 5 minutes until lunch (10:54) | '
                                 '**B LUNCH ONLY**: session 3 ends now, 5 minutes until session 4 (10:54)'),
                    ('10:54:00', '10:54 -- **A LUNCH ONLY**: lunch starts now, ends 11:25 | **B LUNCH ONLY**: '
                                 'session 4 starts now, ends 11:49'),
                    ('11:25:00', '11:25 -- **A LUNCH ONLY**: lunch ends now, 5 minutes until session 4 (11:30) | '
                                 '**B LUNCH ONLY**: session 4 ends in 24 minutes (11:49)'),
                    ('11:30:00', '11:30 -- **A LUNCH ONLY**: session 4 starts now, ends 12:25 | **B LUNCH ONLY**: '
                                 'session 4 ends in 19 minutes (11:49)'),
                    ('11:49:00', '11:49 -- **A LUNCH ONLY**: session 4 ends in 36 minutes (12:25) | **B LUNCH ONLY**: '
                                 'session 4 ends now, 5 minutes until lunch (11:54)'),
                    ('11:54:00', '11:54 -- **A LUNCH ONLY**: session 4 ends in 31 minutes (12:25) | **B LUNCH ONLY**:'
                                 ' lunch starts now, ends 12:25'),
                    ('12:25:00', '12:25 -- **A LUNCH ONLY**: session 4 ends now, 5 minutes until session 5 (12:30) | '
                                 '**B LUNCH ONLY**: lunch ends now, 5 minutes until session 5 (12:30)'),
                    ('12:25:00', '12:25 -- session 4 ends now -- 5 minutes until session 5 (12:30)'),
                    ('12:30:00', '12:30 -- session 5 starts now -- ends 1:25'),
                    ('13:25:00', '1:25 -- session 5 ends now -- 5 minutes until session 6 (1:30)'),
                    ('13:30:00', '1:30 -- session 6 starts now -- ends 2:25'),
                    ('14:25:00', '2:25 -- session 6 ends now -- have a good day!')]

        elif type == 'early':
            return [('07:40:00', '7:40 -- homeroom starts in 5 minutes'),
                    ('07:45:00', '7:45 -- homeroom starts now -- ends 7:49'),
                    ('07:49:00', '7:49 -- homeroom ends now -- 5 minutes until session 1 (7:54)'),
                    ('07:54:00', '7:54 -- session 1 starts now -- ends 8:27'),
                    ('08:27:00', '8:27 -- session 1 ends now -- 5 minutes until session 2 (8:32)'),
                    ('08:32:00', '8:32 -- session 2 starts now -- ends 9:05'),
                    ('09:05:00', '9:05 -- session 2 ends now -- 5 minutes until session 3 (9:10)'),
                    ('09:10:00', '9:10 -- session 3 starts now -- ends 9:43'),
                    ('09:43:00', '9:43 -- session 3 ends now -- 5 minutes until session 4 (9:48) '
                                 '(Lunch A/Class OR Class/Lunch B) (1 hour 8 minutes)'),
                    ('09:48:00', '9:48 -- session 4 starts now (Lunch A/Class OR Class/Lunch B) '
                                 '(1 hour 8 minutes) -- ends 10:56'), ('10:56:00', '10:56 -- session 4 ends now -- '
                                                                                   '5 minutes until session 5 (11:01)'),
                    ('11:01:00', '11:01 -- session 5 starts now -- ends 11:34'),
                    ('11:34:00', '11:34 -- session 5 ends now -- 5 minutes until session 6 (11:39)'),
                    ('11:39:00', '11:39 -- session 6 starts now -- ends 12:12'),
                    ('14:25:00', '2:25 -- session 6 ends now -- have a good day!')]

        elif type == "extended":
            if day == 0:
                return [('07:40:00', '7:40 -- homeroom starts in 5 minutes'),
                       ('07:45:00', '7:45 -- homeroom starts now (22 minutes) -- ends 8:07'),
                        ('08:07:00', '8:07 -- homeroom ends now -- 4 minutes until period 1 (8:11)'),
                       ('08:11:00', '8:11 -- period 1 starts now -- ends 8:50'),
                        ('08:50:00', '8:50 -- period 1 ends now -- 4 minutes until period 2 (8:54)'),
                       ('08:54:00', '8:54 -- period 2 starts now -- ends 9:33'),
                        ('09:33:00', '9:33 -- period 2 ends now -- 4 minutes until period 3 (9:37)'),
                       ('09:37:00', '9:37 -- period 3 starts now -- ends 10:16'),
                        ('10:16:00', '10:16 -- period 3 ends now -- 4 minutes until period 4 (10:20)'),
                       ('10:20:00', '10:20 -- period 4 starts now -- ends 10:59'),
                        ('10:59:00', '10:59 -- period 4 ends now -- 4 minutes until period 5 (11:03) '
                                     '(1 hour 13 minutes) (see below) \n Lunch A=11:03-11:33 / Period 5=11:37-12:16 '
                                     '\n OR \n Class=11:03-11:42 / Lunch B=11:46-12:16'),
                       ('11:03:00', '11:03 -- period 5 starts now (Lunch A/Class OR Class/Lunch B) '
                                    '(1 hour 13 minutes) -- ends 12:16'),
                        ('12:16:00', '12:16 -- period 5 ends now -- 4 minutes until period 6 (12:20)'),
                       ('12:20:00', '12:20 -- period 6 starts now -- ends 12:59'),
                        ('12:59:00', '12:59 -- period 6 ends now -- 4 minutes until period 7 (1:03)'),
                       ('13:03:00', '1:03 -- period 7 starts now -- ends 1:42'),
                        ('13:42:00', '1:42 -- period 7 ends now -- 4 minutes until period 8 (1:46)'),
                       ('13:46:00', '1:46 -- period 8 starts now -- ends 2:25'),
                        ('14:25:00', '2:25 -- period 8 ends now -- one day down!')]
            return [('07:40:00', '7:40 -- homeroom starts in 5 minutes'),
                    ('07:45:00', '7:45 -- homeroom starts now (28 minutes) -- ends 8:13'),
                    ('08:13:00', '8:13 -- homeroom ends now -- 5 minutes until session 1 (8:18)'),
                    ('08:18:00', '8:18 -- session 1 starts now -- ends 9:09'),
                    ('09:09:00', '9:09 -- session 1 ends now -- 5 minutes until session 2 (9:14)'),
                    ('09:14:00', '9:14 -- session 2 starts now -- ends 10:05'),
                    ('10:05:00', '10:05 -- session 2 ends now -- 5 minutes until session 3 (10:10)'),
                    ('10:10:00', '10:10 -- session 3 starts now -- ends 11:01'),
                    ('11:01:00', '11:01 -- session 3 ends now -- 5 minutes until session 4 (11:06) '
                                 '(Lunch A/Class OR Class/Lunch B) (1 hour 27 minutes)'),
                    ('11:06:00', '11:06 -- session 4 starts now (Lunch A/Class OR Class/Lunch B) '
                                 '(1 hour 27 minutes) -- ends 12:33'),
                    ('12:33:00', '12:33 -- session 4 ends now -- 5 minutes until session 5 (12:38)'),
                    ('12:38:00', '12:38 -- session 5 starts now -- ends 1:29'),
                    ('13:29:00', '1:29 -- session 5 ends now -- 5 minutes until session 6 (1:29)'),
                    ('13:34:00', '1:34 -- session 6 starts now -- ends 2:25'),
                    ('14:25:00', '2:25 -- session 6 ends now -- have a good day!')]

        elif type == 'testing':
            return []

        elif type == 'delayed':
            return [('09:40:00', '9:40 -- homeroom starts in 5 minutes'),
                    ('09:45:00', '9:45 -- homeroom starts now -- ends 9:50'),
                    ('09:50:00', '9:50 -- homeroom ends now -- 4 minutes until session 1 (9:54)'),
                    ('09:54:00', '9:54 -- session 1 starts now -- ends 10:30'),
                    ('10:30:00', '10:30 -- session 1 ends now -- 4 minutes until session 2 (10:34)'),
                    ('10:34:00', '10:34 -- session 2 starts now -- ends 11:10'),
                    ('11:10:00', '11:10 -- session 2 ends now -- 4 minutes until session 3 (11:14)'),
                    ('11:14:00', '11:14 -- session 3 starts now -- ends 11:50'),
                    ('11:50:00', '11:50 -- session 3 ends now -- 4 minutes until session 4 (11:54) '
                                 '(Lunch A/Class OR Class/Lunch B) (1 hour 11 minutes)'),
                    ('11:54:00', '11:54 -- session 4 starts now (Lunch A/Class OR Class/Lunch B) '
                                 '(1 hour 11 minutes) -- ends 1:05'),
                    ('13:05:00', '1:05 -- session 4 ends now -- 4 minutes until session 5 (1:09)'),
                    ('13:09:00', '1:09 -- session 5 starts now -- ends 1:45'),
                    ('13:45:00', '1:45 -- session 5 ends now -- 4 minutes until session 6 (1:49)'),
                    ('13:49:00', '1:49 -- session 6 starts now -- ends 2:25'),
                    ('14:25:00', '2:25 -- session 6 ends now -- have a good day!')]

        elif type == 'pep':
            return [('07:40:00', '7:40 -- homeroom starts in 5 minutes'),
                    ('07:45:00', '7:45 -- homeroom starts now -- ends 7:49'),
                    ('07:49:00', '7:49 -- homeroom ends now -- 5 minutes until session 1 (7:54)'),
                    ('07:54:00', '7:54 -- session 1 starts now -- ends 8:38'),
                    ('08:38:00', '8:38 -- session 1 ends now -- 5 minutes until session 2 (8:43)'),
                    ('08:43:00', '8:54 -- session 2 starts now -- ends 9:27'),
                    ('09:27:00', '9:27 -- session 2 ends now -- 5 minutes until session 3 (9:32)'),
                    ('09:32:00', '9:32 -- session 3 starts now -- ends 10:16'),
                    ('10:16:00', '10:16 -- session 3 ends now -- 5 minutes until session 4 (10:21) '
                                 '(Lunch A/Class OR Class/Lunch B) (1 hour 20 minutes)'),
                    ('10:21:00', '10:21 -- session 4 starts now (Lunch A/Class OR Class/Lunch B) '
                                 '(1 hour 20 minutes) -- ends 11:41'),
                    ('11:41:00', '11:41 -- session 4 ends now -- 5 minutes until session 5 (11:46)'),
                    ('11:46:00', '11:46 -- session 5 starts now -- ends 12:30'),
                    ('12:30:00', '12:30 -- session 5 ends now -- 5 minutes until session 6 (12:35)'),
                    ('12:35:00', '12:35 -- session 6 starts now -- ends 1:19'),
                    ('13:19:00', '1:19 -- session 6 ends now -- 5 minutes until PEP RALLY (1:24)'),
                    ('13:24:00', '1:24 -- PEP RALLY starts NOW (1 hour 1 minute) -- ends 2:25'),
                    ('14:25:00', '2:25 -- pep rally ends now -- have a wonderful day!')]
        
        elif type == 'unknown':
            return [('07:40:00', '7:40 -- homeroom starts in 5 minutes'),
                    ('07:45:00', '7:45 -- homeroom starts now -- scheduler is now inactive because the '
                                 'schedule is unknown')]

        else:
            raise Exception('Could not return the specified schedule type in Scheduler (method getSchedule)')

    @staticmethod
    def get_wait_time(future):
        # Wait time in seconds to a future time
        waitTime = 0

        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        currentH = int(current_time.split(':')[0])
        currentM = int(current_time.split(':')[1])
        currentS = int(current_time.split(':')[2])

        futureH = int(future.split(':')[0])
        futureM = int(future.split(':')[1])
        futureS = int(future.split(':')[2])

        future_secs = (futureH*3600) + (futureM*60) + futureS
        current_secs = (currentH*3600) + (currentM*60) + currentS
        waitTime = future_secs-current_secs

        if waitTime <= 0:
            return 0
        else:
            return waitTime


    @tasks.loop(seconds=10)
    async def alerts(self):
        await self.bot.wait_until_ready()
        cur = self.con.cursor()

        waitTime = Scheduler.get_wait_time('07:40:00')

        cur.execute("SELECT working FROM info WHERE id = 1")
        working = cur.fetchall()[0][0]

        weekday = False
        weekno = datetime.datetime.today().weekday()
        if weekno < 5:
            weekday = True
        else:  # 5 Sat, 6 Sun
            pass
            # Weekend

        if ((waitTime != 0 and waitTime < 1800) or (working == 1)) and weekday:

            cur.execute("SELECT day, type FROM info WHERE id = 1")
            x = cur.fetchall()
            day = x[0][0]
            type = x[0][1]

            if working != 1:
                if day == 4:
                    day = 1
                elif day == 0:
                    day = 0
                else:
                    day += 1

            cur.execute("UPDATE info SET day = %s WHERE id = 1", (day,))
            self.con.commit()

            alertMembers = [await self.bot.fetch_user(int(x)) for x in config.alert_list]
            schedule = Scheduler.getSchedule(type, day)

            cur.execute("UPDATE info SET working = 1 WHERE id = 1")
            self.con.commit()

            i = 0
            while i < len(schedule):
                cur.execute("SELECT day, type FROM info WHERE id = 1")
                x = cur.fetchall()[0]
                current_day = x[0]
                current_type = x[1]
                if type != current_type or day != current_day:
                    type = current_type
                    day = current_day
                    schedule = Scheduler.getSchedule(type, day)
                    i = 0
                    continue

                elem = schedule[i]
                self.waitingToward = schedule[i]
                waitTime = Scheduler.get_wait_time(elem[0])

                if waitTime == 0:
                    i += 1
                    continue

                await asyncio.sleep(waitTime)

                for member in alertMembers:
                    try:
                        await member.send(elem[1])
                    except Exception as e:
                        print(f'Error when sending info to a person')
                i += 1

            self.waitingToward = None
            cur.execute("UPDATE info SET working = {0} WHERE id = {1}".format(0, 1))
            self.con.commit()
            cur.close()


def setup(bot):
    bot.add_cog(Scheduler(bot))
