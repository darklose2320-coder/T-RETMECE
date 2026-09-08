from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import requests
import asyncio
import os

# 1. Render'ın uyutmaması için mini web sunucusu
app = Flask('')

@app.route('/')
def home():
    return "Oyun Botu aktif ve çalışıyor!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Discord Bot Ayarları
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- OYUN AYARLARI VE KANALLAR ---
KELIME_KANAL_ID = 1546753719658356878  # Kelime türetmece kanalı
FUTBOL_KANAL_ID = 1546753829087871036  # Futbolcu türetmece kanalı

kelime_oyunu = {
    "son_harf": None,
    "kullanilanlar": set()
}

futbol_oyunu = {
    "son_harf": None,
    "kullanilanlar": set()
}

def tdk_kelime_kontrol(kelime):
    try:
        response = requests.get(f"https://sozluk.gov.tr/gts?ara={kelime.lower()}")
        if response.status_code == 200:
            data = response.json()
            # Düzeltildi: len(data) > 0 şeklinde kontrol ediliyor
            if isinstance(data, list) and len(data) > 0:
                return True
    except Exception as e:
        print(f"TDK Hata: {e}")
    return False

FUTBOLCULAR = {
    "messi", "ronaldo", "mbappe", "haaland", "neymar", "arda", "benzema", 
    "de bruyne", "kante", "lewandowski", "salah", "pele", "maradona", "zidane",
    "icardi", "osimhen", "ferdi", "kerem", "muslera", "torreira", "havertz", "asensio"
}

@bot.event
async def on_ready():
    print(f"{bot.user.name} başarıyla giriş yaptı ve oyunlar için hazır!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # --- 1. KELİME TÜRETMECE OYUNU ---
    if message.channel.id == KELIME_KANAL_ID:
        kelime = message.content.strip().lower()

        if len(kelime.split()) > 1:
            await hata_ver(message, "Lütfen sadece tek bir kelime yazın!")
            return

        if kelime_oyunu["son_harf"] is not None and kelime[0] != kelime_oyunu["son_harf"]:
            await hata_ver(message, f"Kelime '{kelime_oyunu['son_harf']}' harfi ile başlamalı!")
            return

        if kelime in kelime_oyunu["kullanilanlar"]:
            await hata_ver(message, "Bu kelime daha önce yazıldı!")
            return

        if not tdk_kelime_kontrol(kelime):
            await hata_ver(message, "Bu kelime TDK sözlüğünde geçmiyor!")
            return

        kelime_oyunu["kullanilanlar"].add(kelime)
        kelime_oyunu["son_harf"] = kelime[-1]
        await message.add_reaction("✅")
        return

    # --- 2. FUTBOLCU TÜRETMECE OYUNU ---
    if message.channel.id == FUTBOL_KANAL_ID:
        futbolcu = message.content.strip().lower()

        if futbol_oyunu["son_harf"] is not None and futbolcu[0] != futbol_oyunu["son_harf"]:
            await hata_ver(message, f"Futbolcu adı '{futbol_oyunu['son_harf']}' harfi ile başlamalı!")
            return

        if futbolcu in futbol_oyunu["kullanilanlar"]:
            await hata_ver(message, "Bu futbolcu zaten yazıldı!")
            return

        if futbolcu not in FUTBOLCULAR:
            await hata_ver(message, "Böyle tanınmış bir futbolcu listede bulunamadı!")
            return

        futbol_oyunu["kullanilanlar"].add(futbolcu)
        futbol_oyunu["son_harf"] = futbolcu[-1]
        await message.add_reaction("✅")
        return

    await bot.process_commands(message)

async def hata_ver(message, sebep):
    try:
        await message.delete()
    except discord.Forbidden:
        pass
    
    uyari = await message.channel.send(f"{message.author.mention} ❌ {sebep}")
    await asyncio.sleep(4)
    try:
        await uyari.delete()
    except discord.Forbidden:
        pass

# 3. Web sunucusunu başlat ve botu çalıştır
keep_alive()
bot.run(os.getenv("BOT_TOKEN"))
