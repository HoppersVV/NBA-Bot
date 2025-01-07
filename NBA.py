import discord
from discord.ext import commands
from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import leaguegamefinder, TeamGameLog
from datetime import datetime, timedelta
import pytz
from config import TOKEN
import asyncio
import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEAM_EMOJIS = {
    'ATL': '🦅', 'BOS': '☘️', 'BKN': '🌃', 'CHA': '🐝', 'CHI': '🐂',
    'CLE': '⚔️', 'DAL': '🐎', 'DEN': '⛏️', 'DET': '🔧', 'GSW': '🌉',
    'HOU': '🚀', 'IND': '🏎️', 'LAC': '⛵', 'LAL': '💜', 'MEM': '🐻',
    'MIA': '🔥', 'MIL': '🦌', 'MIN': '🐺', 'NOP': '⚜️', 'NYK': '🗽',
    'OKC': '⚡', 'ORL': '🎪', 'PHI': '🔔', 'PHX': '☀️', 'POR': '⌚',
    'SAC': '👑', 'SAS': '🎯', 'TOR': '🦖', 'UTA': '🎷', 'WAS': '🎭'
}

TEAM_COLORS = {
    'ATL': 0xE03A3E, 'BOS': 0x007A33, 'BKN': 0x000000, 'CHA': 0x1D1160,
    'CHI': 0xCE1141, 'CLE': 0x860038, 'DAL': 0x00538C, 'DEN': 0x0E2240,
    'DET': 0xC8102E, 'GSW': 0x1D428A, 'HOU': 0xCE1141, 'IND': 0x002D62,
    'LAC': 0xC8102E, 'LAL': 0x552583, 'MEM': 0x5D76A9, 'MIA': 0x98002E,
    'MIL': 0x00471B, 'MIN': 0x0C2340, 'NOP': 0x0C2340, 'NYK': 0x006BB6,
    'OKC': 0x007AC1, 'ORL': 0x0077C0, 'PHI': 0x006BB6, 'PHX': 0x1D1160,
    'POR': 0xE03A3E, 'SAC': 0x5A2D81, 'SAS': 0xC4CED4, 'TOR': 0xCE1141,
    'UTA': 0x002B5C, 'WAS': 0x002B5C
}

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'{bot.user} connected to Discord')
    await bot.change_presence(activity=discord.Game(name="!commands for help"))

def create_game_embed(game):
    home_team = game['homeTeam']
    away_team = game['awayTeam']
    home_emoji = TEAM_EMOJIS.get(home_team['teamTricode'], '')
    away_emoji = TEAM_EMOJIS.get(away_team['teamTricode'], '')
    
    color = TEAM_COLORS.get(home_team['teamTricode'], 0x000000)
    
    embed = discord.Embed(
        title=f"{away_emoji} {away_team['teamName']} @ {home_team['teamName']} {home_emoji}",
        color=color,
        timestamp=datetime.now()
    )
    
    score_text = f"**{away_team['score']} - {home_team['score']}**"
    period = game['period']
    game_clock = game.get('gameClock', '')
    
    status_text = f"Q{period} {game_clock}" if game['gameStatus'] == 2 else game['gameStatusText']
    
    embed.add_field(name="Score", value=score_text, inline=False)
    embed.add_field(name="Status", value=status_text, inline=False)
    
    if 'leadChanges' in game:
        stats = f"Lead Changes: {game['leadChanges']}\nTimes Tied: {game['timesTied']}"
        embed.add_field(name="Game Stats", value=stats, inline=False)
    
    embed.set_footer(text="Data provided by NBA API • Developed by HoppersVV")
    return embed

@bot.command()
async def scores(ctx):
    board = scoreboard.ScoreBoard()
    games = board.get_dict()['scoreboard']['games']
    
    if not games:
        embed = discord.Embed(
            title="No Games Today",
            description="There are no NBA games scheduled for today.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Data provided by NBA API • Developed by HoppersVV")
        await ctx.send(embed=embed)
        return

    for game in games:
        embed = create_game_embed(game)
        await ctx.send(embed=embed)

@bot.command()
async def schedule(ctx, days: int = 7):
    days = min(max(1, days), 14)
    gamefinder = leaguegamefinder.LeagueGameFinder()
    today = datetime.now(pytz.UTC)
    future_date = today + timedelta(days=days)
    
    games = gamefinder.get_dict()['resultSets'][0]['rowSet']
    upcoming_games = [g for g in games if datetime.strptime(g[5], '%Y-%m-%d') > today.date()]
    
    embed = discord.Embed(
        title=f"📅 Next {days} Days of NBA Games",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    current_date = None
    games_text = ""
    
    for game in upcoming_games[:days * 5]:
        game_date = datetime.strptime(game[5], '%Y-%m-%d')
        if current_date != game_date.date():
            if games_text:
                embed.add_field(name=current_date.strftime('%A, %B %d'), value=games_text, inline=False)
                games_text = ""
            current_date = game_date.date()
        
        home_team = game[6].split()[-1]
        away_team = game[7].split()[-1]
        home_emoji = TEAM_EMOJIS.get(home_team, '')
        away_emoji = TEAM_EMOJIS.get(away_team, '')
        
        games_text += f"{away_emoji} {game[7]} @ {game[6]} {home_emoji}\n"
    
    if games_text:
        embed.add_field(name=current_date.strftime('%A, %B %d'), value=games_text, inline=False)
    
    embed.set_footer(text="Data provided by NBA API • Developed by HoppersVV")
    await ctx.send(embed=embed)

@bot.command()
async def commands(ctx):
    embed = discord.Embed(
        title="🏀 NBA Bot Commands",
        description="Here are all available commands:",
        color=discord.Color.blue()
    )
    
    commands = {
        "!scores": "View today's NBA games and live scores",
        "!schedule [days]": "See upcoming games (default: 7 days, max: 14)",
        "!commands": "Show this help message"
    }
    
    for cmd, desc in commands.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="Data provided by NBA API • Developed by HoppersVV")
    await ctx.send(embed=embed)

bot.run(TOKEN)
