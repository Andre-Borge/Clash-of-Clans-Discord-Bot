import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import os
import asyncio
from dotenv import load_dotenv
from discord.errors import NotFound

load_dotenv()
COC_API_KEY = os.getenv("COC_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

headers = {"Authorization": f"Bearer {COC_API_KEY}"}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

GUILD_ID = 1371206811901890682
CHANNEL_ID = 1387429772023562260
CLAN_INFO_MESSAGE_ID = 1387433042548756672
STATUS_CHANNEL_ID = 1387771579328630856

CLANS = {
    "Royal Legion": {
        "name": "Royal Legion",
        "tag": "#2J8G20C22",
        "description": "A competitive clan focused on war and league.",
    }
}

async def fetch_clan_data_async(clan_tag):
    def fetch():
        encoded_tag = clan_tag.replace("#", "%23")
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                "level": data.get("clanLevel"),
                "members": data.get("members"),
                "description": data.get("description", "No description available"),
                "war_Wins": data.get("warWins"),
                "war_Losses": data.get("warLosses"),
                "war_Ties": data.get("warTies"),
                # there is more data you can fetch, check out the Clash of Clans API documentation for more details.
            }
        else:
            print(f"Error fetching clan {clan_tag}: {response.status_code}")
            return None
    return await asyncio.to_thread(fetch)
# all events
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False
        

    

    
    async def update_clan_data_loop(self):
    
        await self.wait_until_ready()
        while not self.is_closed():
            print("Fetching clan data...")
            for clan_key, clan_info in CLANS.items():
                api_data = await fetch_clan_data_async(clan_info["tag"])
                if api_data:
                    clan_info.update(api_data)
            print("Clan data updated.")
            royal_legion = CLANS["Royal Legion"]

            try:
                channel = self.get_channel(CHANNEL_ID)
                message = await channel.fetch_message(CLAN_INFO_MESSAGE_ID)
                clans_desc = ""
                for clan in CLANS.values():
                    clans_desc += (
                        f"**{clan['name']}** (Level {clan.get('level', 'N/A')}, "
                        f"{clan.get('members', 'N/A')} members)\n"
                        f"{clan['description']}\n\n"
                    )
                embed = discord.Embed(
                    title="**The Royal Legion Clans**",
                    description=clans_desc,
                    color=0x96f348
                )
                embed.add_field( # basic embed 
                    name="__What We Offer__",
                    value=(
                        "Casual\n"
                        "Event Only\n"
                        "<:LeagueCurrency:1387480098793459844>CWL Only Clans\n"
                        "Farming War alliance Clans\n"
                        "<a:CocFigth:1387480028089946323>Competitive Focused\n"
                        "Feeder Clans Supporting other Clans\n"
                        "Clans on trial\n"
                        f"Level: {royal_legion.get('level', 'N/A')}\n"
                        "*To check out the details of our Clans, please press the buttons attached to this embed!*"
                    )
                )
                embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else None)
                embed.set_image(
                    url="https://cdn.discordapp.com/attachments/1387441529181962260/1387442953215279329/placeholder.png" #Placeholder image, replace with actual image if needed. Can also be removed.
                )
                #await message.edit(embed=embed)
                print("Embed updated with latest clan data.")
                await message.edit(embed=embed, view=ClanDropdownView())
            except Exception as e:
                print(f"Failed to update embed: {e}")
            await asyncio.sleep(6 * 3600)  # Every 6 hours

    # the visual status report
    def generate_status_report(self):
        print("status report sent")
        return "**Placeholder**"
    # status report func
    @tasks.loop(minutes=60)
    async def status_report(self):
        await self.wait_until_ready()
        channel = self.get_channel(STATUS_CHANNEL_ID)
        if channel:
            report = self.generate_status_report()
            await channel.send(report)
        else:
            print("Report Channel Not found.")

    # quick /clear command to clear a channel for all of its messages(useful in development). 
    @app_commands.command(name="clear", description="simple command that removes all the previous messages sent in a channel")
    async def clear(interaction: discord.Interaction, amount: int = 10):
        await interaction.response.defer()
        await interaction.channel.purge(limit=amount + 1)

        try:
            await interaction.followup.send(f"Cleared {amount} messages", ephemeral=True)
        except NotFound:
            print("Could not send follow-up, interaction message was deleted(/clear command)")
    
    async def setup_hook(self):
        self.tree.add_command(self.clear)
        
        self.bg_task = asyncio.create_task(self.update_clan_data_loop())
        self.status_report.start()
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        

    # everything that happends on startup
    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print("report ")
        channel = self.get_channel(CHANNEL_ID)
        await self.tree.sync()

# Dropdown Menu For clans
class ClanDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Royal Legion", description="View Royal Legion clan details"),
            discord.SelectOption(label="Royal Dukedome", description="View Royal Dukedome clan details"),
            # here you can add more clans based on your needs, clans mentioned are only examples. These clans will show up in the embed dropdown menu.
        ]
        super().__init__(placeholder="Choose a clan to view.....", min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        selected_clan = self.values[0]
        clan_info = CLANS.get(selected_clan)

        if clan_info:
            embed = discord.Embed(
                title=f"{clan_info['name']} Info",
                description=clan_info.get("description", "No description"),
                color=0x96f348
            )
            embed.add_field(name="**Clan Level**", value=clan_info.get("\nlevel", "N/A"))
            embed.add_field(name="Members", value=clan_info.get("members", "N/A"))


            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Clan not found.", ephemeral=True)
class ClanDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ClanDropdown())


    

# quick /clear command to clear a channel for all of its messages(useful in development)
@bot.command()
async def clear (ctx, amount = 5):
    await ctx.channel.purge (limit = amount)
    await ctx.send (f"Cleared {amount} messages!")



async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync()
bot = MyBot()


    

bot.run(DISCORD_TOKEN)





