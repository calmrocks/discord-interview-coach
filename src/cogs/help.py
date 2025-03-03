import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')  # Remove default help command

    @commands.command(name='help')
    async def help_command(self, ctx, command_name: str = None):
        if command_name:
            # Provide help for a specific command
            command = self.bot.get_command(command_name.lower())
            if command:
                embed = discord.Embed(title=f"Help: {command.name}", color=discord.Color.blue())
                embed.add_field(name="Description", value=command.help or "No description available.", inline=False)
                embed.add_field(name="Usage", value=f"`!{command.name} {command.signature}`", inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Command '{command_name}' not found.")
        else:
            # Provide a list of all commands
            embed = discord.Embed(title="Bot Commands", color=discord.Color.blue())

            # Group commands by cog
            cog_commands = {}
            for command in self.bot.commands:
                cog_name = command.cog_name or "No Category"
                if cog_name not in cog_commands:
                    cog_commands[cog_name] = []
                cog_commands[cog_name].append(command)

            # Add fields for each cog and its commands
            for cog_name, commands_list in cog_commands.items():
                commands_text = "\n".join([f"`{cmd.name}` - {cmd.help or 'No description available.'}"
                                           for cmd in commands_list])
                embed.add_field(name=cog_name, value=commands_text, inline=False)

            embed.set_footer(text="Type !help <command> for more info on a specific command.")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))