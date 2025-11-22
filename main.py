import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# File to store data
DATA_FILE = 'bot_data.json'

# REPLACE THIS WITH YOUR ROLE ID
ALLOWED_ROLE_ID = 1430482528254296134  # Replace with your actual role ID

# Load data from file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'embed_config': {
            'title': '',
            'color': '#5865F2',
            'footer': '',
            'thumbnail': '',
            'image': '',
            'author_name': '',
            'author_icon': ''
        }
    }

# Save data to file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize data
data = load_data()

# Ensure all keys exist
if 'embed_config' not in data:
    data['embed_config'] = {
        'title': '',
        'color': '#5865F2',
        'footer': '',
        'thumbnail': '',
        'image': '',
        'author_name': '',
        'author_icon': ''
    }

# Convert hex color to discord.Color
def hex_to_color(hex_string):
    hex_string = hex_string.lstrip('#')
    return discord.Color(int(hex_string, 16))

# Check if user has the required role (for prefix commands)
def has_required_role():
    async def predicate(ctx):
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return False
        
        role = ctx.guild.get_role(ALLOWED_ROLE_ID)
        if role is None:
            await ctx.send("❌ Required role not found. Please contact an administrator.")
            return False
        
        if role in ctx.author.roles:
            return True
        else:
            await ctx.send("❌ You don't have permission to use this command.")
            return False
    
    return commands.check(predicate)

# Check if user has the required role (for slash commands)
async def has_role_check(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return False
    
    role = interaction.guild.get_role(ALLOWED_ROLE_ID)
    if role is None:
        await interaction.response.send_message("❌ Required role not found. Please contact an administrator.", ephemeral=True)
        return False
    
    if role in interaction.user.roles:
        return True
    else:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return False

# Create embed with current configuration
def create_embed(message_content):
    config = data['embed_config']
    
    embed = discord.Embed(
        description=message_content,
        color=hex_to_color(config.get('color', '#5865F2'))
    )
    
    if config.get('title'):
        embed.title = config['title']
    
    if config.get('footer'):
        embed.set_footer(text=config['footer'])
    
    if config.get('thumbnail'):
        embed.set_thumbnail(url=config['thumbnail'])
    
    if config.get('image'):
        embed.set_image(url=config['image'])
    
    if config.get('author_name'):
        if config.get('author_icon'):
            embed.set_author(name=config['author_name'], icon_url=config['author_icon'])
        else:
            embed.set_author(name=config['author_name'])
    
    return embed

@bot.event
async def on_ready():
    print(f'{bot.user} is now running!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# ==================== EMBED CONFIGURATION COMMANDS ====================

@bot.tree.command(name="embedconfig", description="Configure embed appearance (color, title, footer, etc.)")
@app_commands.describe(
    color="Embed color in hex format (e.g., #FF5733, #00FF00)",
    title="Embed title (leave empty to remove)",
    footer="Footer text (leave empty to remove)",
    thumbnail="Thumbnail image URL (leave empty to remove)",
    image="Large image URL (leave empty to remove)",
    author_name="Author name (leave empty to remove)",
    author_icon="Author icon URL (leave empty to remove)"
)
async def slash_embed_config(
    interaction: discord.Interaction,
    color: str = None,
    title: str = None,
    footer: str = None,
    thumbnail: str = None,
    image: str = None,
    author_name: str = None,
    author_icon: str = None
):
    if not await has_role_check(interaction):
        return
    
    config = data['embed_config']
    changes = []
    
    if color is not None:
        color = color.lstrip('#')
        if len(color) == 6:
            try:
                int(color, 16)
                config['color'] = f'#{color}'
                changes.append(f"Color: #{color}")
            except ValueError:
                await interaction.response.send_message("❌ Invalid hex color format!", ephemeral=True)
                return
        else:
            await interaction.response.send_message("❌ Color must be 6 hex digits!", ephemeral=True)
            return
    
    if title is not None:
        config['title'] = title
        changes.append(f"Title: {title if title else 'Removed'}")
    
    if footer is not None:
        config['footer'] = footer
        changes.append(f"Footer: {footer if footer else 'Removed'}")
    
    if thumbnail is not None:
        config['thumbnail'] = thumbnail
        changes.append(f"Thumbnail: {'Set' if thumbnail else 'Removed'}")
    
    if image is not None:
        config['image'] = image
        changes.append(f"Image: {'Set' if image else 'Removed'}")
    
    if author_name is not None:
        config['author_name'] = author_name
        changes.append(f"Author: {author_name if author_name else 'Removed'}")
    
    if author_icon is not None:
        config['author_icon'] = author_icon
        changes.append(f"Author Icon: {'Set' if author_icon else 'Removed'}")
    
    save_data(data)
    
    response_embed = discord.Embed(
        title="✅ Embed Configuration Updated",
        color=hex_to_color(config['color'])
    )
    
    if changes:
        response_embed.add_field(name="Changes Made", value="\n".join(changes), inline=False)
    
    response_embed.add_field(name="Current Settings", value=(
        f"**Color:** {config['color']}\n"
        f"**Title:** {config['title'] if config['title'] else 'None'}\n"
        f"**Footer:** {config['footer'] if config['footer'] else 'None'}\n"
        f"**Thumbnail:** {'Set' if config['thumbnail'] else 'None'}\n"
        f"**Image:** {'Set' if config['image'] else 'None'}\n"
        f"**Author:** {config['author_name'] if config['author_name'] else 'None'}"
    ), inline=False)
    
    await interaction.response.send_message(embed=response_embed)

@bot.command(name='embedconfig')
@has_required_role()
async def embed_config(ctx, setting: str = None, *, value: str = None):
    """Configure embed appearance"""
    if not setting:
        config = data['embed_config']
        embed = discord.Embed(
            title="📋 Current Embed Configuration",
            color=hex_to_color(config['color'])
        )
        embed.add_field(name="Settings", value=(
            f"**Color:** {config['color']}\n"
            f"**Title:** {config['title'] if config['title'] else 'None'}\n"
            f"**Footer:** {config['footer'] if config['footer'] else 'None'}\n"
            f"**Thumbnail:** {'Set' if config['thumbnail'] else 'None'}\n"
            f"**Image:** {'Set' if config['image'] else 'None'}\n"
            f"**Author:** {config['author_name'] if config['author_name'] else 'None'}"
        ), inline=False)
        await ctx.send(embed=embed)
        return
    
    setting = setting.lower()
    config = data['embed_config']
    
    if setting == 'color':
        if not value:
            await ctx.send("❌ Please provide a hex color")
            return
        value = value.lstrip('#')
        if len(value) == 6:
            try:
                int(value, 16)
                config['color'] = f'#{value}'
                await ctx.send(f"✅ Color set to #{value}")
            except ValueError:
                await ctx.send("❌ Invalid hex color!")
        else:
            await ctx.send("❌ Color must be 6 hex digits!")
    elif setting in ['title', 'footer', 'thumbnail', 'image', 'author_name', 'author_icon']:
        config[setting] = value if value else ''
        await ctx.send(f"✅ {setting.replace('_', ' ').title()} {'set' if value else 'removed'}")
    else:
        await ctx.send("❌ Invalid setting!")
        return
    
    save_data(data)

# ==================== EMBED SENDING COMMANDS ====================

@bot.command(name='sendembed')
@has_required_role()
async def send_embed_cmd(ctx, *, description: str):
    """Send a custom embed"""
    embed = create_embed(description)
    await ctx.send(embed=embed)

@bot.command(name='showconfig')
@has_required_role()
async def show_config(ctx):
    """Display current configuration"""
    embed = discord.Embed(
        title="📋 Current Embed Configuration",
        color=hex_to_color(data['embed_config']['color'])
    )
    
    config = data['embed_config']
    embed.add_field(name="Settings", value=(
        f"**Color:** {config['color']}\n"
        f"**Title:** {config['title'] if config['title'] else 'None'}\n"
        f"**Footer:** {config['footer'] if config['footer'] else 'None'}\n"
        f"**Thumbnail:** {'Set' if config['thumbnail'] else 'None'}\n"
        f"**Image:** {'Set' if config['image'] else 'None'}\n"
        f"**Author:** {config['author_name'] if config['author_name'] else 'None'}"
    ), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def custom_help(ctx):
    """Display all commands"""
    embed = discord.Embed(
        title="🤖 Discord Embed Bot Commands",
        description="Send custom embeds with configurable appearance",
        color=hex_to_color(data['embed_config']['color'])
    )
    
    commands_info = [
        ("embedconfig", "Configure embed appearance (color, title, footer, images, author)"),
        ("sendembed <text>", "Send a custom embed with your text"),
        ("showconfig", "Display current embed configuration"),
        ("help", "Show this help message")
    ]
    
    for cmd, desc in commands_info:
        embed.add_field(name=f"!{cmd} or /{cmd}", value=desc, inline=False)
    
    embed.add_field(
        name="💡 Example Usage",
        value=(
            "1. Configure appearance:\n"
            "`/embedconfig color:#FF5733 title:My Title footer:My Footer`\n\n"
            "2. Send embed:\n"
            "`/sendembed This is my custom message!`"
        ),
        inline=False
    )
    
    await ctx.send(embed=embed)

# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="sendembed", description="Send a custom embed")
@app_commands.describe(description="Embed description/content")
async def slash_send_embed(interaction: discord.Interaction, description: str):
    if not await has_role_check(interaction):
        return
    
    embed = create_embed(description)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="showconfig", description="Display current embed configuration")
async def slash_show_config(interaction: discord.Interaction):
    if not await has_role_check(interaction):
        return
    
    embed = discord.Embed(
        title="📋 Current Embed Configuration",
        color=hex_to_color(data['embed_config']['color'])
    )
    
    config = data['embed_config']
    embed.add_field(name="Settings", value=(
        f"**Color:** {config['color']}\n"
        f"**Title:** {config['title'] if config['title'] else 'None'}\n"
        f"**Footer:** {config['footer'] if config['footer'] else 'None'}\n"
        f"**Thumbnail:** {'Set' if config['thumbnail'] else 'None'}\n"
        f"**Image:** {'Set' if config['image'] else 'None'}\n"
        f"**Author:** {config['author_name'] if config['author_name'] else 'None'}"
    ), inline=False)
    
    await interaction.response.send_message(embed=embed)

# Run the bot
bot.run('MTQ0MTYzMTAyODQ4NDc3MTk1MQ.Gvt926.AHYj0U5GPAMAr1deypoTO722oUnq2B7BQormX4')