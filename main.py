from typing import Final
import os
import time
import discord
import manga as mg
import anime as am
import urllib.parse
from dotenv import load_dotenv
from discord import Intents, Client, app_commands
from discord.ext import tasks, commands
import datetime

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

intents: Intents = Intents.default()
client: Client = Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready() -> None:
    try:
        manga_scheduled_update.start()
        anime_scheduled_update.start()
        print(f'{client.user} is now running!')
        channel = client.get_channel(1268223325415673981)
        await channel.send("I am online now")
    except Exception as e:
        print(e)

@tree.command(name="manga_search", description="search for a manga")
@app_commands.describe(manga="the ID of the manga (check URL on manhuagui)")
async def manga_search(interaction: discord.Interaction, manga: str):
    await interaction.response.defer()
    try:
        output = await mg.find_manga(int(manga))
    except Exception:
        await interaction.followup.send("wrong ID")
    await interaction.followup.send(output)

@tree.command(name="manga_add", description="add a manga to your subscription list (10 second cooldown)")
@app_commands.describe(manga="the ID of the manga (check URL on manhuagui)")
async def manga_add(interaction: discord.Interaction, manga: str):
    await interaction.response.defer()
    addTitle = await mg.add_manga(manga, interaction.user.id)
    if(addTitle != ''):
        await interaction.followup.send(f'{addTitle} added!') 
    else:
        await interaction.followup.send('failed to add the manga')

@tree.command(name="manga_list", description="list all manga in your subscription list")
@app_commands.describe(start="the starting line number of the list", end="the ending line number of the list")
async def manga_list(interaction: discord.Interaction, start: int, end: int):
    await interaction.response.send_message(mg.list_manga(interaction.user.id, start, end))

@tree.command(name="manga_remove", description="remove a manga from your subscription list")
@app_commands.describe(manga="the ID of the manga")
async def manga_remove(interaction: discord.Interaction, manga: str):
    removeTitle = mg.remove_manga(manga, interaction.user.id) 
    if(removeTitle != ''):
        await interaction.response.send_message(f'{removeTitle} removed!') 
    else:
        await interaction.response.send_message('failed to remove the manga')

@tree.command(name="manga_reset", description="reset your subscription list")
async def manga_reset(interaction: discord.Interaction):
    success = mg.reset_manga(interaction.user.id)
    if(success):
        await interaction.response.send_message(f'list reset!') 
    else:
        await interaction.response.send_message('failed to remove the manga')

@tree.command(name="manga_update", description="update your subscription list")
async def manga_update(interaction: discord.Interaction):
    await interaction.response.defer()
    back = await mg.update_manga(interaction.user.id)
    if(back != ''):
        await interaction.followup.send(back) 
    else:
        await interaction.followup.send('nothing is updated')

@tree.command(name="manga_sort", description="sort your manga subscription list by update time")
async def manga_sort(interaction: discord.Interaction):
    await interaction.response.defer()
    back = mg.sort_manga(interaction.user.id)
    if(back != ''):
        await interaction.followup.send(back) 
    else:
        await interaction.followup.send('failed to sort')

@tree.command(name="manga_gen", description="generate a link to the manga with the provided ID")
@app_commands.describe(manga="manga ID")
async def manga_gen(interaction: discord.Interaction, manga: str):
    await interaction.response.send_message(f'https://m.manhuagui.com/comic/{manga}') 

@tree.command(name="anime_add", description="add an anime to your subscription list")
@app_commands.describe(anime="the URL to the anime on anime1")
async def anime_add(interaction: discord.Interaction, anime: str):
    url = urllib.parse.unquote(anime)
    await interaction.response.defer()
    addTitle = await am.add_anime(url, interaction.user.id)
    if(addTitle != ''):
        await interaction.followup.send(f'{addTitle} added!') 
    else:
        await interaction.followup.send('failed to add the anime')

@tree.command(name="anime_list", description="list all anime in your subscription list")
@app_commands.describe(start="the starting line number of the list", end="the ending line number of the list")
async def anime_list(interaction: discord.Interaction, start: int, end: int):
    await interaction.response.send_message(am.list_anime(interaction.user.id, start, end), suppress_embeds=True)

@tree.command(name="anime_remove", description="remove an anime from your subscription list")
@app_commands.describe(anime="the name of the anime")
async def anime_remove(interaction: discord.Interaction, anime: str):
    removeTitle = am.remove_anime(anime, interaction.user.id)
    if(removeTitle != ''):
        await interaction.response.send_message(f'{removeTitle} removed!') 
    else:
        await interaction.response.send_message('failed to remove the anime')

@tree.command(name="anime_reset", description="reset your subscription list")
async def anime_reset(interaction: discord.Interaction):
    success = am.reset_anime(interaction.user.id)
    if(success):
        await interaction.response.send_message(f'list reset!') 
    else:
        await interaction.response.send_message('failed to remove the anime')

@tree.command(name="anime_update", description="update your subscription list")
async def anime_update(interaction: discord.Interaction):
    await interaction.response.defer()
    back = await am.update_anime(interaction.user.id)
    if(back != ''):
        await interaction.followup.send(back, suppress_embeds=True) 
    else:
        await interaction.followup.send('nothing is updated')

@tree.command(name="anime_sort", description="sort your anime subscription list by update time")
async def anime_sort(interaction: discord.Interaction):
    await interaction.response.defer()
    back = am.sort_anime(interaction.user.id)
    if(back != ''):
        await interaction.followup.send(back, suppress_embeds=True) 
    else:
        await interaction.followup.send('failed to sort')

@tree.command(name="sync", description="sync commands when updating the script")
async def sync(interaction: discord.Interaction):
    if interaction.user.name == 'dandan0922':
        await tree.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

@tasks.loop(hours= 18)
async def manga_scheduled_update():
    await client.wait_until_ready()
    for filename in os.listdir(".\\manhuagui"):
        if filename.endswith(".txt"):
            user = await client.fetch_user(filename[:-4])
            back = await mg.update_manga(filename[:-4])
            if(back == ''): continue
            msg = f'**Daily manga update for <@{filename[:-4]}>**\n' + f'Date: {datetime.datetime.today().strftime('%Y-%m-%d')}\n' + back
            await user.send(msg, suppress_embeds=True)

@tasks.loop(hours= 18)
async def anime_scheduled_update():
    await client.wait_until_ready()
    for filename in os.listdir(".\\animeone"):
        if filename.endswith(".txt"):
            user = await client.fetch_user(filename[:-4])
            back = await am.update_anime(filename[:-4])
            if(back == ''): continue
            msg = f'**Daily anime update for <@{filename[:-4]}>**\n' + f'Date: {datetime.datetime.today().strftime('%Y-%m-%d')}\n' + back
            await user.send(msg, suppress_embeds=True)

def main() -> None:
    client.run(token=TOKEN)

if __name__ == '__main__':
    main()
