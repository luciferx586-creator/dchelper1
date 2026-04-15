import os
import asyncio
import random
import time
from collections import deque

import aiohttp
import discord

TOKEN = os.getenv("TOKEN")

OWNER_ID = 1387325386991468635
CHANNEL_ID = 1493910285629784154

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

sent_timestamps = []
recent_txids = deque(maxlen=100)

# emojis
TXID = "<:txid:1493903102611558501>"
BTC = "<:btc:1493903325639217322>"
LTC = "<:litecoin:1493903290260262932>"
CHECK = "<:greentick:1488449073475354725>"

NETWORKS = [
    {
        "name": "BTC",
        "emoji": BTC,
        "api": "https://mempool.space/api/mempool/recent",
        "explorer": "https://mempool.space/tx/{}",
        "value_key": "value",
        "unit_divisor": 100_000_000,
    },
    {
        "name": "LTC",
        "emoji": LTC,
        "api": "https://litecoinspace.org/api/mempool/recent",
        "explorer": "https://litecoinspace.org/tx/{}",
        "value_key": "value",
        "unit_divisor": 100_000_000,
    },
]

def can_send():
    global sent_timestamps
    now = time.time()
    sent_timestamps = [t for t in sent_timestamps if now - t < 60]
    return len(sent_timestamps) < 3


def get_weighted_delay():
    r = random.random()

    if r < 0.10:
        return random.randint(60, 360)
    elif r < 0.30:
        return random.randint(420, 900)
    elif r < 0.60:
        return random.randint(960, 1200)
    elif r < 0.75:
        return random.randint(1260, 2400)
    elif r < 0.90:
        return random.randint(2460, 3600)
    else:
        return random.randint(3960, 10800)


def generate_weighted_usd():
    r = random.random()

    if r < 0.02:
        return round(random.uniform(2000, 8000), 2)
    elif r < 0.22:
        return round(random.uniform(500, 2000), 2)
    elif r < 0.72:
        return round(random.uniform(20, 250), 2)
    else:
        return round(random.uniform(250, 500), 2)


async def fetch_recent_tx(session):
    network = random.choice(NETWORKS)

    try:
        async with session.get(network["api"]) as resp:
            data = await resp.json()
    except:
        return None

    if not isinstance(data, list):
        return None

    random.shuffle(data)

    for tx in data:
        txid = tx.get("txid")
        value = tx.get(network["value_key"])

        if not txid or txid in recent_txids or not value:
            continue

        recent_txids.append(txid)

        return {
            "network": network["name"],
            "emoji": network["emoji"],
            "txid": txid,
            "explorer": network["explorer"].format(txid)
        }

    return None


async def get_random_ids(guild):
    members = [m for m in guild.members if not m.bot]

    if len(members) < 2:
        return "Anonymous User", "Anonymous User"

    sender = random.choice(members)
    receiver = random.choice(members)

    return f"`{sender.id}`", f"`{receiver.id}`"


async def send_tx(channel, tx_data):
    guild = channel.guild

    # 25% real users
    if random.random() < 0.25:
        sender, receiver = await get_random_ids(guild)
    else:
        sender, receiver = "Anonymous User", "Anonymous User"

    # controlled amount
    usd = generate_weighted_usd()

    price_map = {
        "BTC": 60000,
        "LTC": 80
    }

    price = price_map.get(tx_data["network"], 100)
    coin = round(usd / price, 8)

    amount_text = f"${usd:,.2f} ({coin:.8f} {tx_data['network']})"

    embed = discord.Embed(
        title=f"{CHECK} {tx_data['network']} Transaction",
        color=0x2b2d31
    )

    embed.add_field(
        name="Amount",
        value=f"{tx_data['emoji']} {amount_text}",
        inline=False
    )

    embed.add_field(
        name="Sender",
        value=sender,
        inline=True
    )

    embed.add_field(
        name="Receiver",
        value=receiver,
        inline=True
    )

    embed.add_field(
        name=f"{TXID} Transaction ID",
        value=f"`{tx_data['txid'][:24]}...`",
        inline=False
    )

    embed.set_footer(text="⚡")

    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="View on Explorer",
        url=tx_data["explorer"]
    ))

    await channel.send(embed=embed, view=view)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    await client.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="transactions"
        )
    )

    channel = client.get_channel(CHANNEL_ID)

    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(get_weighted_delay())

            if not can_send():
                continue

            tx_data = await fetch_recent_tx(session)
            if not tx_data:
                continue

            await send_tx(channel, tx_data)
            sent_timestamps.append(time.time())


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id != OWNER_ID:
        return

    if message.content == "asdfghjkl;'":
        await message.delete()

        channel = client.get_channel(CHANNEL_ID)

        async with aiohttp.ClientSession() as session:
            tx_data = await fetch_recent_tx(session)

        if not tx_data:
            return

        await send_tx(channel, tx_data)


client.run(TOKEN)
