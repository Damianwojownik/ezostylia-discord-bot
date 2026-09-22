import os
import random
import hashlib
from datetime import date, datetime

import discord
from discord import app_commands
from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://integrations.emergentagent.com/llm/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

CTA_TAROT = "🔮 Å½Ã¸Ã©Ã³Ã¸Ã§Ã³ pełny odczyt? Odkryj więcej na ezostylia.com"
CTA_RUNA = "⚔️ Poznaj pełną moc run na ezostylia.com"
CTA_MEDYTACH�H�'̙ Więcej medytacji na ezostylia.com"

# ---------------------------------------------------------------------------
# Tarot deck — full 78 cards
# ---------------------------------------------------------------------------
MAJOR_ARCANA = [
    "Głupiec (The Fool)",
    "Mag (The Magician)",
    "Kapłanka (The High Priestess)",
    "Cesarzowa (The Empress)",
    "Cesarz (The Emperor)",
    "Hierofant (The Hierophant)",
    "Kochankowie (The Lovers)",
    "Rydwan (The Chariot)",
    "Siła (Strength)",
    "Pustelnik (The Hermit)",
    "Koło Fortuny (Wheel of Fortune)",
    "Sprawiedliwość (Justice)",
    "Wisielec (The Hanged Man)",
    "Śmierć (Death)",
    "Wstrzemięźliwość (Temperance)",
    "Diabeł (The Devil)",
    "Wieża (The Tower)",
    "Gwiazda (The Star)",
    "Księżyc (The Moon)",
    "Słońce (The Sun)",
    "Sąd (Judgement)",
    "Świat (The World)",
]

SUITS = ["Buławy (Wands)", "Kielichy (Cups)", "Miecze (Swords)", "Pentakle (Pentacles)"]
RANKS = [
    "As", "Dwójka", "Trójka", "Czwórka", "Piątka", "Szóstka",
    "Siódemka", "Ósemka", "Dziewiątka", "Dziesiątka",
    "Paż", "Rycerz", "Kkólowa", "Krol",
]

MINOR_ARCANA = [f"{rank} {suit}" for suit in SUITS for rank in RANKS]
FULL_DECK = MAJOR_ARCANA + MINOR_ARCANA  # 78 cards

# ---------------------------------------------------------------------------
# Elder Futhark runes —  24
# ---------------------------------------------------------------------------
ELDER_FUTHARK = [
    (" ", "Fehu", "Bogactwo, dostatek, energia materialna"),
    ("ᚂ", "Uruz", "Siła, zdrowie, witalność"),
    ("ᚆ", "Thurisaz", "Ochrona, chaos, przebudzenie"),
    ("ᚈ", "Ansuz", "Mądrość, komunikacja, boskie przesłanie"),
    ("ᚱ", "Raidho", "Podróż, rytm, postęp"),
    ("ᚲ", "Kenaz", "Wiedza, twórczość, oświecenie"),
    ("ᚷ", "Gebo", "Dar, partnerstwo, równowaga"),
    ("ᚹ", "Wunjo", "Radość, harmonia, spełnienie"),
    ("ᚺ", "Hagalaz", "Zniszczenie, transformacja, oczyszczenie"),
    ("ᚾ", "Nauthiz", "Potrzeba, ograniczenie, cierpliwość"),
    ("ᛁ", "Isa", "Lód, zastój, introspekcja"),
    ("ᛃ", "Jera", "Żniwa, cykle, nagroda za wysiłek"),
    ("ᛇ", "Eihwaz", "Obrona, wytrwałość, transformacja"),
    ("ᛈ", "Perthro", "Tajemnica, los, ukryte siły"),
    ("ᛉ", "Algiz", "Ochrona, instynkt, duchowe połączenie"),
    ("ᛊ", "Sowilo", "Słońce, sukces, zwicięstwo"),
    ("ᛏ", "Tiwaz", "Honor, sprawiedliwość, odwaga"),
    ("ᛒ", "Berkano", "Narodziny, wzrost, odnowa"),
    ("ᛖ", "Ehwaz", "Ruch, zaufanie, współpraca"),
    ("ᛗ", "Mannaz", "Ludzkość, jaźń, wspólnota"),
    ("ᛚ", "Laguz", "Woda, intuicja, podświadomość"),
    ("ᛜ", "Ingwaz", "Płodność, potencjał, nowy początek"),
    ("ᛞ", "Dagaz", "Świt, przełom, przebudzenie"),
    ("ᛟ", "Othala", "Dziedzictwo, dom, przynależność"),
]

# ---------------------------------------------------------------------------
# Channels to auto-create on guild join
# ---------------------------------------------------------------------------
AUTO_CHANNELS = [
    "witaj",
    "ogłoszenia",
    "tarot-i-karty",
    "medytacje-i-rytuały",
    "rozwój-duchowy",
    "ai-i-mistycyzm",
    "społeczność",
]

WELCOME_MESSAGE = (
    "🌙⚔️ **Witaj w społeczności Ezostylia!**\n\n"
    "Jestem AI-asystentem Ezostylia. Używaj:\n"
    "• `/tarot` — losuj kartę tarota z interpretacją\n"
    "• `/runa` — losuj runę z znaczeniem\n"
    "• `/medytacja` — dzilnny prompt medytacyjny\n\n"
    "Odkryjrne możliwości na **ezostylia.com** ✨"
)

# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------
llm_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI | None:
    global llm_client
    if llm_client is not None:
        return llm_client
    if not LLM_API_KEY:
        return None
    llm_client = AsyncOpenAI(api_key=LE�_API_KEY, base_url=LLM_BASE_URL)
    return llm_client


async def ask_llm(system_prompt: str, user_prompt: str) -> str | None:
    client = get_llm_client()
    if client is None:
        return None
    try:
        response = await client.chat.completions.create(
            model=LE�_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.8,
        )
        return response.choices[0].message.content
    except Exception as exc:
        print(f"[LLM ERROR] {exc}")
        return None


# ---------------------------------------------------------------------------
# Fallback generators (when LLM unavailable)
# ---------------------------------------------------------------------------
TAROT_FALLBACKS = [
    "Ta karta wskazuje na ważny moment w Twojej podróży duchowej. Siły kosmiczne sprzyjają refleksji i wewnętrznemu wzrostowi. Otwórz się na znaki, które przynosi Ci los.",
    "Karta mówi o nadchodzących zmianach — bądź gotowy na nowe możliwości. Twoja intuicja jest teraz szczególnie silna. Zaufaj swojemu wewnętrznemu głosowi.",
    "Energia tej karty wiąże się z transformacją i odnową. Czas porzucić stare wzorce i otworzyć się na nowe ścieżki. Wszechświat wspiera Twój rozwp�(.",
]

RUNE_FALLBACKS = [
    "Ta runa niesie ze sobą potężną energię transformacji. Skieruj swoją uwagę do wewnątrz i poszukaj odpowiedzi w ciszy. Starożytna mądrość prowadzi Cię na właściwą ścieżkę.",
    "Runa wskazuje na siłę ukrytą w głębi Twojej duszy. Czas na odważne decyzje i zaufanie kosmicznemu porządkowi. Przodkowie czuwają nad Tobą.",
    "Znaczenie tej runy łączy �e z Twoim aktualnym stanem ducha. Otwórz się na przesłanie z wyższych sfer. Energia runicona wspiera Twoje duchowe przebudzenie.",
]

MEDITATION_THEMES = [
    "Wyobraź sobie, że stoisz w starożytnej świątyni otoczonej świecami. Oddychaj głęboko i poczuj jak energia Wszechświata przepływa przez Twoje ciało. Pozwól myślom odpłynąć jak liściom na jesiennym wietrze.",
    "Zamknij oczy i wyobraż sobie noc pełną gwiazd. Każda gwiazda reprezentuje jedną z Twoich wewnętrznych prawd. Wybierz jedną i pozwp� jej światłu ogrzać Twoje serce.",
    "Usiądź wygodnie i zwróć uwagęnna swój oddech. Wyobraź sobie strumień krystalicznie czystej wody, który obmywa Twoją duszę z napięć dnia. Z każdym oddechem czujesz się lżejszy.",
    "Poczuj pod stopami ciepłą ziemię pradawnego lasu. Drzewa szepczą starkżytne mądrości do Twojego serca. Jesteś częścią wielkiego kosmicznego cyklu natury.",
    "Wyobraż sobie, że siedzisz na szczycie góry o wschodzie słońca. Ciepłe promienie budzą w Tobie ukrytą moc. Jesteś gotów na nowy dzień pełen duchowego wzrostu.",
    "Skup się na pulsowaniu swojego serca — każde uderzenie to kosmiczny rytm łącz�cy Cię z Wszechświatem. Pozwól temu rytmowi prowadzić Twoje myśli ku wewnętrznemu spokoj{�.",
    "Zamknij oczy i wyobraź sobie purpurowe światło otaczające Twoje ciało. To światło ochronne oczyszcza Twoją aurę. Oddychaj&�im głęboko i poczuj wewnętrzną harmonię.",
]


def daily_seed() -> int:
    return int(hashlib.md5(str(date.today()).encode()).hexdigest(), 16)


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.guilds = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Ezostylia Bot online as {bot.user} (guilds: {len(bot.guilds)})")


@bot.event
async def on_guild_join(guild: discord.Guild):
    existing = {ch.name for ch in guild.text_channels}
    witaj_channel = None

    for ch_name in AUTO_CHANNELS:
        if ch_name not in existing:
            new_ch = await guild.create_text_channel(ch_name)
            if ch_name == "witaj":
                witaj_channel = new_ch
        elif ch_name == "witaj":
            witaj_channel = discord.utils.get(guild.text_channels, name="witaj")

    if witaj_channel:
        await witaj_channel.send(WELCOME_MESSAGE)


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------
@tree.command(name="tarot", description="Losuj kartę tarota z AI interpretacją 🔮")
async def cmd_tarot(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    card = random.choice(FULL_DECK)
    is_reversed = random.choice([True, False])
    position = "odwrócona" if is_reversed else "prosta"

    ai_text = await ask_llm(
        system_prompt=(
            "Jesteś mistycznym interpretatorem tarota. Odpowiadaj po polsku. "
            "Daj krótką, tajemniczą interpretację karty w 3-4 zdaniach. "
            "Nie dodavaj żadnych wezwań do działania ani linkÁw."
        ),
        user_prompt=f"Karta: {card}, pozycja: {position}. Daj interpretację.",
    )

    if ai_text is None:
        ai_text = random.choice(TAROT_FALLBACKS)

    embed = discord.Embed(
        title=f"🃏 {card}",
        description=f"*Pozycja: {position}*\n\n{ai_text}\n\n{CTA_TAROT}",
        color=0x9B59B6,
    )
    embed.set_footer(text="Ezostylia • ezostylia.com")
    await interaction.followup.send(embed=embed)


@tree.command(name="runa", description="Losuj runę Elder Futhark z AI znaczeniem —️")
async def cmd_runa(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    symbol, name, keywords = random.choice(ELDER_FUTHARK)

    ai_text = await ask_llm(
        system_prompt=(
            "Jesteś starożytnym mistrzem run. Odpowiadaj po polsku. "
            "Daj krótkie, mistyczne znaczenie runy w 3-4 zdaniach. "
            "Nie dodavaj żadnych wezwań do działania ani linkÁw."
        ),
        user_prompt=f"Runa: {name} ({symbol}), słowa kluczowe: {keywords}. Opisz jej znaczenie.",
    )

    if ai_text is None:
        ai_text = random.choice(RUNE_FALLBACKS)

    embed = discord.Embed(
        title=f"{symbol} {name}",
        description=f"*{keywords}*\n\n{ai_text}\n\n{CTA_RUNA}",
        color=0xE67E22,
    )
    embed.set_footer(text="Ezostylia • ezostylia.com")
    await interaction.followup.send(embed=embed)


@tree.command(name="medytacja", description="Dzienny prompt medytacyjny 🌙")
async def cmd_medytacja(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    seed = daily_seed()
    rng = random.Random(seed)
    theme_idx = rng.randint(0, len(MEDITATION_THEMES) - 1)

    ai_text = await ask_llm(
        system_prompt=(
            "Jesteś duchowym przewodnikiem medytacji. Odpowiadaj po polsku. "
            "Stwórz erótki, inspirujący prompt medytacyjny w 2-3 zdaniach. "
            "Bądź mistyczny i poetycki. Nie dodawaj żadnych wezwań do działania ani linkÁw."
        ),
        user_prompt=f"Stwórz prompt medytacyjny na dziq ({date.today().isoformat()}). Motyw przewodni: duchowe przebudzenie i wewnętrzna siła.",
    )

    if ai_text is None:
        ai_text = MEDITATION_THEMES[theme_idx]

    embed = discord.Embed(
        title="🧘 Medytacja dnia",
        description=f"{ai_text}\n\n{CTA_MEDYTACKA}",
        color=0x2ECC71,
    )
    embed.set_footer(text=f"Ezostylia • {date.today().strftime('%d.%m.%Y')} • ezostylia.com")
    await interaction.followup.send(embed=embed)


@tree.command(name="help", description="Lista komend Ezostylia bota 📖")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Komendy Ezostylia Bot",
        description=(
            "🃏 **`/tarot`** — Losuj kartę tarota z mistyczną interpretacją AI\n\n"
            "⚔️ **`/runa`** — Losuj runę Elder Futhark z AI znaczeniem\n\n"
            "🧘 **`/medytacja`** — Dzilnny prompt medytacyjny (zmienia się codziennie)\n\n"
            "📖 **`/help`** — Ta wiadomość\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🌙 Odkryj pełne możliwości na **ezostylia.com** ✨"
        ),
        color=0x3498DB,
    )
    embed.set_footer(text="Ezostylia • Twoje duchowe centrum AI")
    await interaction.response.send_message(embed=embed)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
