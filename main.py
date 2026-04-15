import discord
import random
import asyncio
import time
import os
import aiohttp

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1493910285629784154  # replace with your channel id

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

sent_timestamps = []
recent_txids = []

# emojis
FAST = "<a:25801:1493897362672713768>"
TXID = "<:txid:1493903102611558501>"
BTC = "<:btc:1493903325639217322>"
LTC = "<:litecoin:1493903290260262932>"
ETH = "<:ethereum:1493903258693926912>"
USDT = "<:usdtt:1493903360271581184>"
LOCK = "<:lockeddd:1493903007488675910>"
PROFILE = "<:profile:1488441547187027972>"
CHECK = "<:greentick:1488449073475354725>"

# prevent spam (max 3 per min)
def can_send():
    global sent_timestamps
    now = time.time()
    sent_timestamps = [t for t in sent_timestamps if now - t < 60]
    return len(sent_timestamps) < 3

# get random real user
async def get_random_user(guild):
    members = [m for m in guild.members if not m.bot]
    if not members:
        return "Anonymous User"
    return random.choice(members).name

# fetch REAL LTC transactions
async def get_real_transaction():
    url = "https://api.blockcypher.com/v1/ltc/main"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

            txs = data.get("unconfirmed_txrefs", [])

            if not txs:
                return None

            tx = random.choice(txs)

            txid = tx.get("tx_hash")

            # avoid duplicates
            if txid in recent_txids:
                return None

            value_ltc = tx.get("value", 0) / 1e8

            usd = round(value_ltc * random.uniform(70, 90), 2)

            # store recent txids
            recent_txids.append(txid)
            if len(recent_txids) > 20:
                recent_txids.pop(0)

            return {
                "crypto": "LTC",
                "emoji": LTC,
                "amount_crypto": round(value_ltc, 6),
                "amount_usd": usd,
                "txid": txid
            }

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    channel = client.get_channel(CHANNEL_ID)
    guild = channel.guild

    while True:
        wait_time = random.randint(60, 7200)  # 1 min → 2 hrs
        await asyncio.sleep(wait_time)

        if not can_send():
            continue

        tx_data = await get_real_transaction()

        if not tx_data:
            continue

        crypto_name = tx_data["crypto"]
        crypto_emoji = tx_data["emoji"]
        crypto_amt = tx_data["amount_crypto"]
        usd = tx_data["amount_usd"]
        txid = tx_data["txid"]

        # 10% real users
        if random.random() < 0.1:
            sender = await get_random_user(guild)
            receiver = await get_random_user(guild)
        else:
            sender = "Anonymous User"
            receiver = "Anonymous User"

        embed = discord.Embed(
            title=f"{CHECK} {crypto_name} Deal Completed",
            color=0x2b2d31
        )

        embed.add_field(
            name="Amount",
            value=f"{crypto_emoji} ${usd} ({crypto_amt} {crypto_name})",
            inline=False
        )

        embed.add_field(
            name="Sender",
            value=f"{PROFILE} {sender} {LOCK}",
            inline=True
        )

        embed.add_field(
            name="Receiver",
            value=f"{PROFILE} {receiver} {LOCK}",
            inline=True
        )

        embed.add_field(
            name=f"{TXID} Transaction ID",
            value=f"`{txid[:18]}...`",
            inline=False
        )

        embed.set_footer(text=f"{FAST} Exon MM • Live Blockchain Data")

        # real blockchain link
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="View on Blockchain",
            url=f"https://live.blockcypher.com/ltc/tx/{txid}"
        ))

        await channel.send(embed=embed, view=view)

        sent_timestamps.append(time.time())

client.run(TOKEN)
