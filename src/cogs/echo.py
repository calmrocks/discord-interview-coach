from discord.ext import commands

class Echo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='echo')
    async def echo(self, ctx, *, message: str):
        """Repeats what you say"""
        await ctx.send(f"You said: {message}")

async def setup(bot):
    await bot.add_cog(Echo(bot))