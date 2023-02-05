import discord


async def sendSimpleEmbed(channel, text, delete):
    """
    Given a channel, sends default red-colored embed given an embed description with optional deletion
    """
    sent_msg = await channel.send(embed=discord.Embed(description=text, color=0x2596be))
    if delete:
        await sent_msg.delete(delay=10)
    return sent_msg

async def addReactions(message, num):
    """
    Add reactions given a message and number of reactions
    """
    reactions = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
    for n, reaction in enumerate(reactions):
        if n < num:
            await message.add_reaction(reaction)
