from discord.ext import commands, tasks
from bs4 import BeautifulSoup
import requests
import discord
import psycopg2
import config


class DailyPoll(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.con = psycopg2.connect(config.database_url)

    @commands.Cog.listener()
    async def on_ready(self):
        self.dailyPollChannel = self.bot.get_channel(config.daily_poll_channel_id)
        self.print_daily_poll.start()

    @tasks.loop(seconds=9000)
    async def print_daily_poll(self):
        cur = self.con.cursor()

        # Data Scrape #
        pollButtons = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵', '🇶', '🇷', '🇸']
        daily_poll_answers = []
        daily_poll_website_html = requests.get('https://www.swagbucks.com/polls')
        daily_poll_website_string = BeautifulSoup(daily_poll_website_html.text, 'html.parser')
        daily_poll_question = daily_poll_website_string.find('span', attrs={'class': 'pollQuestion'}).text
        daily_poll_answers_html = daily_poll_website_string.find_all('td', attrs={'class': 'indivAnswerText'})

        cur.execute("SELECT prevquestion FROM info WHERE id = 1")
        prevQuestion = cur.fetchall()[0][0]

        # Send the Poll #
        if daily_poll_question != prevQuestion:

            cur.execute("UPDATE info SET prevquestion = %s WHERE id = 1", (daily_poll_question,))
            self.con.commit()

            for x in daily_poll_answers_html:
                daily_poll_answers.append(x.text)
            daily_poll_embed = discord.Embed(title=daily_poll_question, color=0xff0000)
            for x, answer in enumerate(daily_poll_answers):
                daily_poll_embed.add_field(name='\u200b', value=pollButtons[x] + ' ' + answer, inline=False)
            sent_message = await self.dailyPollChannel.send(embed=daily_poll_embed)
            for i in range(len(daily_poll_answers)):
                await sent_message.add_reaction(emoji=pollButtons[i])


def setup(bot):
    bot.add_cog(DailyPoll(bot))
