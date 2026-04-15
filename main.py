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

client = discord.Client(intents=intents)

sent_timestamps = []
recent_txids = deque(maxlen=100)

# emojis
FAST = "<a:25801:1493897362672713768>"
TXID = "<:txid:1493903102611558501>"
BTC = "<:btc:1493903325639217322>"
LTC = "<:litecoin:1493903290260262932>"
ETH = "<:ethereum:1493903258693926912>"
USDT = "<:usdtt:1493903360271581184>"
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
        return random.randint(60, 360)         # 1–6 min
    elif r < 0.30:
        return random.randint(420, 900)        # 7–15 min
    elif r < 0.60:
        return random.randint(960, 1200)       # 16–20 min
    elif r < 0.75:
        return random.randint(1260, 2400)      # 21–40 min
    elif r < 0.90:
        return random.randint(2460, 3600)      # 41–60 min
    else:
        return random.randint(3960, 10800)     # 1.1–3 hr


async def fetch_price_usd(session, symbol):
    ids = {"BTC": "bitcoin", "LTC": "litecoin"}
    coin_id = ids.get(symbol)

    if not coin_id:
        return None

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"

    try:
        async with session.get(url) as resp:
            data = await resp.json()
            return data[coin_id]["usd"]
    except:
        return None


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

        amount_coin = value / network["unit_divisor"]

        if amount_coin <= 0:
            continue

        usd_price = await fetch_price_usd(session, network["name"])
        amount_usd = round(amount_coin * usd_price, 2) if usd_price else None

        recent_txids.append(txid)

        return {
            "network": network["name"],
            "emoji": network["emoji"],
            "txid": txid,
            "amount_coin": amount_coin,
            "amount_usd": amount_usd,
            "explorer": network["explorer"].format(txid)
        }

    return None


def format_amount(coin, usd, symbol):
    if usd:
        return f"${usd:,.2f} ({coin:.8f} {symbol})"
    return f"{coin:.8f} {symbol}"


async def send_tx(channel, tx_data, footer_text):
    embed = discord.Embed(
        title=f"{CHECK} {tx_data['network']} Transaction",
        color=0x2b2d31
    )

    embed.add_field(
        name="Amount",
        value=f"{tx_data['emoji']} {format_amount(tx_data['amount_coin'], tx_data['amount_usd'], tx_data['network'])}",
        inline=False
    )

    embed.add_field(
        name=f"{TXID} Transaction ID",
        value=f"`{tx_data['txid'][:24]}...`",
        inline=False
    )

    embed.set_footer(text=f"{FAST} {footer_text}")

    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="View on Explorer",
        url=tx_data["explorer"]
    ))

    await channel.send(embed=embed, view=view)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    # 🔥 Status set
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

            await send_tx(channel, tx_data, "Live Feed")
            sent_timestamps.append(time.time())


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id != OWNER_ID:
        return

    if message.content == "asdfghjkl;'":
        channel = client.get_channel(CHANNEL_ID)

        async with aiohttp.ClientSession() as session:
            tx_data = await fetch_recent_tx(session)

        if not tx_data:
            await message.channel.send("No transaction found.")
            return

        await send_tx(channel, tx_data, "Manual Trigger")


client.run(TOKEN)
