import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Config
GUILD_ID = 1395452995256320000  # Replace with your actual server ID (int)
VOUCH_CHANNEL_ID = 1395458850206912573

# Roles for permission checks
OWNER_STAFF_ROLES = ["Owner", "Staff"]
VOUCH_ALLOWED_ROLES = ["Owner", "Staff", "Customer"]
VOUCHABLE_ROLES = ["Owner", "Staff"]  # Only these can be vouched/checked

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# In-memory vouch database (resets on bot restart)
vouches_db = {}

def has_roles(user_roles, allowed_roles):
    return any(role.name in allowed_roles for role in user_roles)

# Permission check for who can run /bought, /role (Owner or Staff only)
def has_owner_staff_role(interaction: discord.Interaction) -> bool:
    return has_roles(interaction.user.roles, OWNER_STAFF_ROLES)

# Permission check for who can run /vouch (Owner, Staff or Customer)
def has_vouch_permission(interaction: discord.Interaction) -> bool:
    return has_roles(interaction.user.roles, VOUCH_ALLOWED_ROLES)

# Check if the target user has allowed roles for vouch/check
def target_has_allowed_role(user: discord.Member) -> bool:
    return has_roles(user.roles, VOUCHABLE_ROLES)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("✅ Slash commands synced to server.")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# ----------------------
# /bought Command
# ----------------------
@bot.tree.command(name="bought", description="Give a user the 'Customer' role.")
@app_commands.describe(user="The user to give the role to")
async def bought(interaction: discord.Interaction, user: discord.Member):
    if not has_owner_staff_role(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    role = discord.utils.get(interaction.guild.roles, name="Customer")
    if role:
        try:
            await user.add_roles(role)
            await interaction.response.send_message(f"✅ {user.mention} has been given the Customer role.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to assign that role.")
    else:
        await interaction.response.send_message("❌ Role 'Customer' not found.")

# ----------------------
# /role Command
# ----------------------
@bot.tree.command(name="role", description="Assign any role to a user.")
@app_commands.describe(user="The user to give the role to", role_name="The exact name of the role")
async def role(interaction: discord.Interaction, user: discord.Member, role_name: str):
    if not has_owner_staff_role(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if role:
        try:
            await user.add_roles(role)
            await interaction.response.send_message(f"✅ {user.mention} has been given the `{role_name}` role.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to assign that role.")
    else:
        await interaction.response.send_message(f"❌ Role `{role_name}` not found.")

# ----------------------
# /vouch Command
# ----------------------
@bot.tree.command(name="vouch", description="Vouch for a user with a reason. Owner/Staff/Customer only in specific channel.")
@app_commands.describe(user="User you want to vouch for", reason="Reason for vouch")
async def vouch(interaction: discord.Interaction, user: discord.Member, reason: str):
    # Check caller permission
    if not has_vouch_permission(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command here.", ephemeral=True)
        return

    # Check channel restriction
    if interaction.channel.id != VOUCH_CHANNEL_ID:
        await interaction.response.send_message(f"❌ This command can only be used in <#{VOUCH_CHANNEL_ID}>.", ephemeral=True)
        return

    # Check target user roles
    if not target_has_allowed_role(user):
        await interaction.response.send_message(
            f"❌ You can only vouch for users with the roles: {', '.join(VOUCHABLE_ROLES)}.", ephemeral=True
        )
        return

    user_id = str(user.id)
    vouches_db[user_id] = vouches_db.get(user_id, 0) + 1

    await interaction.response.send_message(
        f"✅ {interaction.user.mention} vouched for {user.mention} with reason: \"{reason}\".\n"
        f"{user.mention} now has **{vouches_db[user_id]}** vouches."
    )

# ----------------------
# /vouches Command
# ----------------------
@bot.tree.command(name="vouches", description="Check how many vouches a user has.")
@app_commands.describe(user="User to check vouches for")
async def vouches(interaction: discord.Interaction, user: discord.Member):
    # Only users with allowed roles can be checked
    if not target_has_allowed_role(user):
        await interaction.response.send_message(
            f"❌ You can only check vouches for users with the roles: {', '.join(VOUCHABLE_ROLES)}.", ephemeral=True
        )
        return

    count = vouches_db.get(str(user.id), 0)
    await interaction.response.send_message(f"📊 {user.mention} has **{count}** vouches.")


@bot.tree.command(name="prices", description="Display the R6 boosting price list.")
async def prices(interaction: discord.Interaction):
    if not has_owner_staff_role(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    embed = discord.Embed(title="💰 Prices", color=discord.Color.red())
    embed.add_field(name="Copper", value=(
        "Copper → Bronze = £7\n"
        "Copper → Silver = £14\n"
        "Copper → Gold = £21\n"
        "Copper → Platinum = £28\n"
        "Copper → Emerald = £35\n"
        "Copper → Diamond = £42\n"
        "Copper → Champion = £49"
    ), inline=False)

    embed.add_field(name="Bronze", value=(
        "Bronze → Silver = £7\n"
        "Bronze → Gold = £14\n"
        "Bronze → Platinum = £21\n"
        "Bronze → Emerald = £28\n"
        "Bronze → Diamond = £35\n"
        "Bronze → Champion = £42"
    ), inline=False)

    embed.add_field(name="Silver", value=(
        "Silver → Gold = £7\n"
        "Silver → Platinum = £14\n"
        "Silver → Emerald = £21\n"
        "Silver → Diamond = £28\n"
        "Silver → Champion = £35"
    ), inline=False)

    embed.add_field(name="Gold", value=(
        "Gold → Platinum = £7\n"
        "Gold → Emerald = £14\n"
        "Gold → Diamond = £21\n"
        "Gold → Champion = £28"
    ), inline=False)

    embed.add_field(name="Platinum", value=(
        "Platinum → Emerald = £7\n"
        "Platinum → Diamond = £14\n"
        "Platinum → Champion = £21"
    ), inline=False)

    embed.add_field(name="Emerald", value=(
        "Emerald → Diamond = £7\n"
        "Emerald → Champion = £14"
    ), inline=False)

    embed.add_field(name="Diamond", value="Diamond → Champion = £7", inline=False)

    await interaction.response.send_message(embed=embed)


# ----------------------
# Run the bot
# ----------------------

bot.run(TOKEN)

