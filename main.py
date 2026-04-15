import discord
import random
import asyncio
import time
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 123456789012345678  # replace with your channel id

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

sent_timestamps = []

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

cryptos = [
    ("BTC", BTC, 60000),
    ("LTC", LTC, 80),
    ("ETH", ETH, 3000),
    ("USDT", USDT, 1)
]

def generate_txid():
    return ''.join(random.choices('abcdef0123456789', k=64))

def generate_amount(price):
    usd = round(random.uniform(2, 100), 2)
    crypto = round(usd / price, 8)
    return usd, crypto

def can_send():
    global sent_timestamps
    now = time.time()
    sent_timestamps = [t for t in sent_timestamps if now - t < 60]
    return len(sent_timestamps) < 3

async def get_random_user(guild):
    members = [m for m in guild.members if not m.bot]
    if not members:
        return "Anonymous User"
    return random.choice(members).name

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    channel = client.get_channel(CHANNEL_ID)
    guild = channel.guild

    while True:
        wait_time = random.randint(60, 7200)
        await asyncio.sleep(wait_time)

        if not can_send():
            continue

        crypto_name, crypto_emoji, price = random.choice(cryptos)
        usd, crypto_amt = generate_amount(price)
        txid = generate_txid()

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

        embed.set_footer(text=f"{FAST} Exon MM • Secure Transaction")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="View on Blockchain",
            url=f"https://blockchair.com/search?q={txid}"
        ))

        await channel.send(embed=embed, view=view)

        sent_timestamps.append(time.time())

client.run(TOKEN)
