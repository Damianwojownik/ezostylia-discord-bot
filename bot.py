import json
import os
import pathlib
import random
import hashlib
from datetime import date, datetime
from typing import Literal

import discord
from discord import app_commands
from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://integrations.emergentagent.com/llm/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

SUPPORTED_LANGS = ("pl", "en", "de")
DEFAULT_LANG = "pl"

Lang = Literal["pl", "en", "de"]

# ---------------------------------------------------------------------------
# Per-user language preferences  (user_id -> lang code)
# Persisted to a JSON file so prefs survive restarts.
# ---------------------------------------------------------------------------
PREFS_PATH = pathlib.Path(os.environ.get("PREFS_PATH", "user_lang_prefs.json"))

_user_lang_prefs: dict[int, str] = {}


def _load_prefs() -> None:
    global _user_lang_prefs
    if PREFS_PATH.exists():
        try:
            _user_lang_prefs = {int(k): v for k, v in json.loads(PREFS_PATH.read_text()).items()}
        except Exception:
            _user_lang_prefs = {}


def _save_prefs() -> None:
    try:
        PREFS_PATH.write_text(json.dumps({str(k): v for k, v in _user_lang_prefs.items()}))
    except Exception as exc:
        print(f"[PREFS] save error: {exc}")


def set_user_lang(user_id: int, lang: str) -> None:
    _user_lang_prefs[user_id] = lang
    _save_prefs()


def get_user_lang(user_id: int, guild_locale: str | None = None) -> str:
    if user_id in _user_lang_prefs:
        return _user_lang_prefs[user_id]
    return detect_lang_from_locale(guild_locale)


def detect_lang_from_locale(locale: str | None) -> str:
    if not locale:
        return DEFAULT_LANG
    code = str(locale).lower().replace("-", "_")
    if code.startswith("de"):
        return "de"
    if code.startswith("en"):
        return "en"
    if code.startswith("pl"):
        return "pl"
    return DEFAULT_LANG


_load_prefs()

# ---------------------------------------------------------------------------
# Internationalised strings
# ---------------------------------------------------------------------------
I18N: dict[str, dict[str, str]] = {
    # CTAs
    "cta_tarot": {
        "pl": "🔮 Chcesz pełny odczyt? Odkryj więcej na ezostylia.com",
        "en": "🔮 Want a full reading? Discover more at ezostylia.com",
        "de": "🔮 Möchtest du ein vollständiges Reading? Entdecke mehr auf ezostylia.com",
    },
    "cta_runa": {
        "pl": "⚔️ Poznaj pełną moc run na ezostylia.com",
        "en": "⚔️ Discover the full power of runes at ezostylia.com",
        "de": "⚔️ Entdecke die volle Kraft der Runen auf ezostylia.com",
    },
    "cta_medytacja": {
        "pl": "🌙 Więcej medytacji na ezostylia.com",
        "en": "🌙 More meditations at ezostylia.com",
        "de": "🌙 Mehr Meditationen auf ezostylia.com",
    },
    # Tarot embed
    "position_label": {"pl": "Pozycja", "en": "Position", "de": "Position"},
    "position_upright": {"pl": "prosta", "en": "upright", "de": "aufrecht"},
    "position_reversed": {"pl": "odwrócona", "en": "reversed", "de": "umgekehrt"},
    # Meditation embed
    "meditation_title": {"pl": "🧘 Medytacja dnia", "en": "🧘 Meditation of the day", "de": "🧘 Meditation des Tages"},
    # Help
    "help_title": {
        "pl": "📖 Komendy Ezostylia Bot",
        "en": "📖 Ezostylia Bot Commands",
        "de": "📖 Ezostylia Bot Befehle",
    },
    "help_body": {
        "pl": (
            "🃏 **`/tarot`** — Losuj kartę tarota z mistyczną interpretacją AI\n\n"
            "⚔️ **`/runa`** — Losuj runę Elder Futhark z AI znaczeniem\n\n"
            "🧘 **`/medytacja`** — Dzienny prompt medytacyjny (zmienia się codziennie)\n\n"
            "🌐 **`/language`** — Zmień język bota (pl / en / de)\n\n"
            "📖 **`/help`** — Ta wiadomość\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🌙 Odkryj pełne możliwości na **ezostylia.com** ✨"
        ),
        "en": (
            "🃏 **`/tarot`** — Draw a tarot card with a mystical AI interpretation\n\n"
            "⚔️ **`/runa`** — Draw an Elder Futhark rune with AI meaning\n\n"
            "🧘 **`/medytacja`** — Daily meditation prompt (changes every day)\n\n"
            "🌐 **`/language`** — Change bot language (pl / en / de)\n\n"
            "📖 **`/help`** — This message\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🌙 Discover the full experience at **ezostylia.com** ✨"
        ),
        "de": (
            "🃏 **`/tarot`** — Ziehe eine Tarotkarte mit mystischer KI-Deutung\n\n"
            "⚔️ **`/runa`** — Ziehe eine Elder-Futhark-Rune mit KI-Bedeutung\n\n"
            "🧘 **`/medytacja`** — Täglicher Meditationsimpuls (wechselt täglich)\n\n"
            "🌐 **`/language`** — Bot-Sprache ändern (pl / en / de)\n\n"
            "📖 **`/help`** — Diese Nachricht\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🌙 Entdecke das volle Erlebnis auf **ezostylia.com** ✨"
        ),
    },
    "help_footer": {
        "pl": "Ezostylia • Twoje duchowe centrum AI",
        "en": "Ezostylia • Your spiritual AI centre",
        "de": "Ezostylia • Dein spirituelles KI-Zentrum",
    },
    # Language command
    "lang_set": {
        "pl": "🌐 Język ustawiony na **polski** 🇵🇱",
        "en": "🌐 Language set to **English** 🇬🇧",
        "de": "🌐 Sprache auf **Deutsch** eingestellt 🇩🇪",
    },
    "lang_invalid": {
        "pl": "❌ Nieznany język. Użyj: `pl`, `en` lub `de`.",
        "en": "❌ Unknown language. Use: `pl`, `en` or `de`.",
        "de": "❌ Unbekannte Sprache. Verwende: `pl`, `en` oder `de`.",
    },
}


def t(key: str, lang: str) -> str:
    entry = I18N.get(key, {})
    return entry.get(lang, entry.get(DEFAULT_LANG, key))


# ---------------------------------------------------------------------------
# Tarot deck — full 78 cards, trilingual names
# ---------------------------------------------------------------------------
MAJOR_ARCANA_I18N: list[dict[str, str]] = [
    {"pl": "Głupiec", "en": "The Fool", "de": "Der Narr"},
    {"pl": "Mag", "en": "The Magician", "de": "Der Magier"},
    {"pl": "Kapłanka", "en": "The High Priestess", "de": "Die Hohepriesterin"},
    {"pl": "Cesarzowa", "en": "The Empress", "de": "Die Herrscherin"},
    {"pl": "Cesarz", "en": "The Emperor", "de": "Der Herrscher"},
    {"pl": "Hierofant", "en": "The Hierophant", "de": "Der Hierophant"},
    {"pl": "Kochankowie", "en": "The Lovers", "de": "Die Liebenden"},
    {"pl": "Rydwan", "en": "The Chariot", "de": "Der Wagen"},
    {"pl": "Siła", "en": "Strength", "de": "Die Kraft"},
    {"pl": "Pustelnik", "en": "The Hermit", "de": "Der Eremit"},
    {"pl": "Koło Fortuny", "en": "Wheel of Fortune", "de": "Das Rad des Schicksals"},
    {"pl": "Sprawiedliwość", "en": "Justice", "de": "Die Gerechtigkeit"},
    {"pl": "Wisielec", "en": "The Hanged Man", "de": "Der Gehängte"},
    {"pl": "Śmierć", "en": "Death", "de": "Der Tod"},
    {"pl": "Wstrzemieźliwość", "en": "Temperance", "de": "Die Mäßigkeit"},
    {"pl": "Diabeł", "en": "The Devil", "de": "Der Teufel"},
    {"pl": "Wieża", "en": "The Tower", "de": "Der Turm"},
    {"pl": "Gwiazda", "en": "The Star", "de": "Der Stern"},
    {"pl": "Księżyc", "en": "The Moon", "de": "Der Mond"},
    {"pl": "Słońce", "en": "The Sun", "de": "Die Sonne"},
    {"pl": "Sąd", "en": "Judgement", "de": "Das Gericht"},
    {"pl": "Świat", "en": "The World", "de": "Die Welt"},
]

SUITS_I18N: list[dict[str, str]] = [
    {"pl": "Buławy", "en": "Wands", "de": "Stäbe"},
    {"pl": "Kielichy", "en": "Cups", "de": "Kelche"},
    {"pl": "Miecze", "en": "Swords", "de": "Schwerter"},
    {"pl": "Pentakle", "en": "Pentacles", "de": "Münzen"},
]

RANKS_I18N: list[dict[str, str]] = [
    {"pl": "As", "en": "Ace", "de": "Ass"},
    {"pl": "Dwójka", "en": "Two", "de": "Zwei"},
    {"pl": "Trójka", "en": "Three", "de": "Drei"},
    {"pl": "Czwórka", "en": "Four", "de": "Vier"},
    {"pl": "Piątka", "en": "Five", "de": "Fünf"},
    {"pl": "Szóstka", "en": "Six", "de": "Sechs"},
    {"pl": "Siódemka", "en": "Seven", "de": "Sieben"},
    {"pl": "Ósemka", "en": "Eight", "de": "Acht"},
    {"pl": "Dziewiątka", "en": "Nine", "de": "Neun"},
    {"pl": "Dziesiątka", "en": "Ten", "de": "Zehn"},
    {"pl": "Paź", "en": "Page", "de": "Bube"},
    {"pl": "Rycerz", "en": "Knight", "de": "Ritter"},
    {"pl": "Królowa", "en": "Queen", "de": "Königin"},
    {"pl": "Król", "en": "King", "de": "König"},
]

# Build index-based deck so we can resolve names per-language at draw time
DECK_SIZE = len(MAJOR_ARCANA_I18N) + len(SUITS_I18N) * len(RANKS_I18N)  # 78


def card_name(index: int, lang: str) -> str:
    if index < len(MAJOR_ARCANA_I18N):
        return MAJOR_ARCANA_I18N[index][lang]
    minor_idx = index - len(MAJOR_ARCANA_I18N)
    suit_idx = minor_idx // len(RANKS_I18N)
    rank_idx = minor_idx % len(RANKS_I18N)
    return f"{RANKS_I18N[rank_idx][lang]} {SUITS_I18N[suit_idx][lang]}"


# Backward-compat flat lists used only by legacy helpers / tests
MAJOR_ARCANA = [m["pl"] for m in MAJOR_ARCANA_I18N]
SUITS = [s["pl"] for s in SUITS_I18N]
RANKS = [r["pl"] for r in RANKS_I18N]
MINOR_ARCANA = [f"{r} {s}" for s in SUITS for r in RANKS]
FULL_DECK = MAJOR_ARCANA + MINOR_ARCANA

# ---------------------------------------------------------------------------
# Elder Futhark runes — 24, trilingual keywords
# ---------------------------------------------------------------------------
ELDER_FUTHARK_I18N: list[tuple[str, str, dict[str, str]]] = [
    ("ᚠ", "Fehu",     {"pl": "Bogactwo, dostatek, energia materialna",       "en": "Wealth, abundance, material energy",          "de": "Reichtum, Fülle, materielle Energie"}),
    ("ᚢ", "Uruz",     {"pl": "Siła, zdrowie, witalność",                     "en": "Strength, health, vitality",                  "de": "Stärke, Gesundheit, Vitalität"}),
    ("ᚦ", "Thurisaz", {"pl": "Ochrona, chaos, przebudzenie",                 "en": "Protection, chaos, awakening",                "de": "Schutz, Chaos, Erwachen"}),
    ("ᚨ", "Ansuz",    {"pl": "Mądrość, komunikacja, boskie przesłanie",      "en": "Wisdom, communication, divine message",       "de": "Weisheit, Kommunikation, göttliche Botschaft"}),
    ("ᚱ", "Raidho",   {"pl": "Podróż, rytm, postęp",                        "en": "Journey, rhythm, progress",                   "de": "Reise, Rhythmus, Fortschritt"}),
    ("ᚲ", "Kenaz",    {"pl": "Wiedza, twórczość, oświecenie",                "en": "Knowledge, creativity, enlightenment",         "de": "Wissen, Kreativität, Erleuchtung"}),
    ("ᚷ", "Gebo",     {"pl": "Dar, partnerstwo, równowaga",                  "en": "Gift, partnership, balance",                  "de": "Gabe, Partnerschaft, Gleichgewicht"}),
    ("ᚹ", "Wunjo",    {"pl": "Radość, harmonia, spełnienie",                 "en": "Joy, harmony, fulfilment",                    "de": "Freude, Harmonie, Erfüllung"}),
    ("ᚺ", "Hagalaz",  {"pl": "Zniszczenie, transformacja, oczyszczenie",     "en": "Destruction, transformation, purification",   "de": "Zerstörung, Transformation, Reinigung"}),
    ("ᚾ", "Nauthiz",  {"pl": "Potrzeba, ograniczenie, cierpliwość",          "en": "Need, constraint, patience",                  "de": "Bedürfnis, Einschränkung, Geduld"}),
    ("ᛁ", "Isa",      {"pl": "Lód, zastój, introspekcja",                    "en": "Ice, stillness, introspection",               "de": "Eis, Stillstand, Innenschau"}),
    ("ᛃ", "Jera",     {"pl": "Żniwa, cykle, nagroda za wysiłek",            "en": "Harvest, cycles, reward for effort",           "de": "Ernte, Zyklen, Belohnung für Anstrengung"}),
    ("ᛇ", "Eihwaz",   {"pl": "Obrona, wytrwałość, transformacja",            "en": "Defence, endurance, transformation",           "de": "Verteidigung, Ausdauer, Transformation"}),
    ("ᛈ", "Perthro",  {"pl": "Tajemnica, los, ukryte siły",                  "en": "Mystery, fate, hidden forces",                "de": "Geheimnis, Schicksal, verborgene Kräfte"}),
    ("ᛉ", "Algiz",    {"pl": "Ochrona, instynkt, duchowe połączenie",        "en": "Protection, instinct, spiritual connection",  "de": "Schutz, Instinkt, spirituelle Verbindung"}),
    ("ᛊ", "Sowilo",   {"pl": "Słońce, sukces, zwycięstwo",                   "en": "Sun, success, victory",                       "de": "Sonne, Erfolg, Sieg"}),
    ("ᛏ", "Tiwaz",    {"pl": "Honor, sprawiedliwość, odwaga",                "en": "Honour, justice, courage",                    "de": "Ehre, Gerechtigkeit, Mut"}),
    ("ᛒ", "Berkano",  {"pl": "Narodziny, wzrost, odnowa",                    "en": "Birth, growth, renewal",                      "de": "Geburt, Wachstum, Erneuerung"}),
    ("ᛖ", "Ehwaz",    {"pl": "Ruch, zaufanie, współpraca",                   "en": "Movement, trust, cooperation",                "de": "Bewegung, Vertrauen, Zusammenarbeit"}),
    ("ᛗ", "Mannaz",   {"pl": "Ludzkość, jaźń, wspólnota",                    "en": "Humanity, self, community",                   "de": "Menschheit, Selbst, Gemeinschaft"}),
    ("ᛚ", "Laguz",    {"pl": "Woda, intuicja, podświadomość",                "en": "Water, intuition, subconscious",              "de": "Wasser, Intuition, Unterbewusstsein"}),
    ("ᛜ", "Ingwaz",   {"pl": "Płodność, potencjał, nowy początek",           "en": "Fertility, potential, new beginning",          "de": "Fruchtbarkeit, Potenzial, neuer Anfang"}),
    ("ᛞ", "Dagaz",    {"pl": "Świt, przełom, przebudzenie",                  "en": "Dawn, breakthrough, awakening",               "de": "Morgendämmerung, Durchbruch, Erwachen"}),
    ("ᛟ", "Othala",   {"pl": "Dziedzictwo, dom, przynależność",              "en": "Heritage, home, belonging",                   "de": "Erbe, Heimat, Zugehörigkeit"}),
]

# Backward-compat tuple list (symbol, name, pl_keywords)
ELDER_FUTHARK = [(s, n, kw["pl"]) for s, n, kw in ELDER_FUTHARK_I18N]

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
    "• `/medytacja` — dzienny prompt medytacyjny\n"
    "• `/language` — zmień język (pl / en / de)\n\n"
    "Odkryj pełne możliwości na **ezostylia.com** ✨"
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
    llm_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return llm_client


async def ask_llm(system_prompt: str, user_prompt: str) -> str | None:
    client = get_llm_client()
    if client is None:
        return None
    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
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
# LLM system-prompt fragments per language
# ---------------------------------------------------------------------------
LANG_INSTRUCTION: dict[str, str] = {
    "pl": "Odpowiadaj po polsku.",
    "en": "Answer in English.",
    "de": "Antworte auf Deutsch.",
}

TAROT_SYSTEM: dict[str, str] = {
    "pl": "Jesteś mistycznym interpretatorem tarota. {lang} Daj krótką, tajemniczą interpretację karty w 3-4 zdaniach. Nie dodawaj żadnych wezwań do działania ani linków.",
    "en": "You are a mystical tarot interpreter. {lang} Give a short, mysterious card interpretation in 3-4 sentences. Do not add any calls to action or links.",
    "de": "Du bist ein mystischer Tarot-Deuter. {lang} Gib eine kurze, geheimnisvolle Kartendeutung in 3-4 Sätzen. Füge keine Handlungsaufforderungen oder Links hinzu.",
}

TAROT_USER: dict[str, str] = {
    "pl": "Karta: {card}, pozycja: {position}. Daj interpretację.",
    "en": "Card: {card}, position: {position}. Give an interpretation.",
    "de": "Karte: {card}, Position: {position}. Gib eine Deutung.",
}

RUNE_SYSTEM: dict[str, str] = {
    "pl": "Jesteś starożytnym mistrzem run. {lang} Daj krótkie, mistyczne znaczenie runy w 3-4 zdaniach. Nie dodawaj żadnych wezwań do działania ani linków.",
    "en": "You are an ancient rune master. {lang} Give a short, mystical rune meaning in 3-4 sentences. Do not add any calls to action or links.",
    "de": "Du bist ein alter Runenmeister. {lang} Gib eine kurze, mystische Runenbedeutung in 3-4 Sätzen. Füge keine Handlungsaufforderungen oder Links hinzu.",
}

RUNE_USER: dict[str, str] = {
    "pl": "Runa: {name} ({symbol}), słowa kluczowe: {keywords}. Opisz jej znaczenie.",
    "en": "Rune: {name} ({symbol}), keywords: {keywords}. Describe its meaning.",
    "de": "Rune: {name} ({symbol}), Schlüsselwörter: {keywords}. Beschreibe ihre Bedeutung.",
}

MEDITATION_SYSTEM: dict[str, str] = {
    "pl": "Jesteś duchowym przewodnikiem medytacji. {lang} Stwórz krótki, inspirujący prompt medytacyjny w 2-3 zdaniach. Bądź mistyczny i poetycki. Nie dodawaj żadnych wezwań do działania ani linków.",
    "en": "You are a spiritual meditation guide. {lang} Create a short, inspiring meditation prompt in 2-3 sentences. Be mystical and poetic. Do not add any calls to action or links.",
    "de": "Du bist ein spiritueller Meditationsführer. {lang} Erstelle einen kurzen, inspirierenden Meditationsimpuls in 2-3 Sätzen. Sei mystisch und poetisch. Füge keine Handlungsaufforderungen oder Links hinzu.",
}

MEDITATION_USER: dict[str, str] = {
    "pl": "Stwórz prompt medytacyjny na dziś ({date}). Motyw przewodni: duchowe przebudzenie i wewnętrzna siła.",
    "en": "Create a meditation prompt for today ({date}). Theme: spiritual awakening and inner strength.",
    "de": "Erstelle einen Meditationsimpuls für heute ({date}). Thema: spirituelles Erwachen und innere Stärke.",
}

# ---------------------------------------------------------------------------
# Fallback generators (when LLM unavailable) — trilingual
# ---------------------------------------------------------------------------
TAROT_FALLBACKS: dict[str, list[str]] = {
    "pl": [
        "Ta karta wskazuje na ważny moment w Twojej podróży duchowej. Siły kosmiczne sprzyjają refleksji i wewnętrznemu wzrostowi. Otwórz się na znaki, które przynosi Ci los.",
        "Karta mówi o nadchodzących zmianach — bądź gotowy na nowe możliwości. Twoja intuicja jest teraz szczególnie silna. Zaufaj swojemu wewnętrznemu głosowi.",
        "Energia tej karty wiąże się z transformacją i odnową. Czas porzucić stare wzorce i otworzyć się na nowe ścieżki. Wszechświat wspiera Twój rozwój.",
    ],
    "en": [
        "This card points to a pivotal moment in your spiritual journey. Cosmic forces favour reflection and inner growth. Open yourself to the signs that fate brings you.",
        "The card speaks of coming changes — be ready for new possibilities. Your intuition is especially strong right now. Trust your inner voice.",
        "This card's energy is tied to transformation and renewal. It is time to shed old patterns and open yourself to new paths. The Universe supports your growth.",
    ],
    "de": [
        "Diese Karte weist auf einen wichtigen Moment in deiner spirituellen Reise hin. Kosmische Kräfte begünstigen Reflexion und inneres Wachstum. Öffne dich für die Zeichen, die das Schicksal dir bringt.",
        "Die Karte spricht von kommenden Veränderungen — sei bereit für neue Möglichkeiten. Deine Intuition ist gerade besonders stark. Vertraue deiner inneren Stimme.",
        "Die Energie dieser Karte ist mit Transformation und Erneuerung verbunden. Es ist Zeit, alte Muster loszulassen und sich neuen Wegen zu öffnen. Das Universum unterstützt dein Wachstum.",
    ],
}

RUNE_FALLBACKS: dict[str, list[str]] = {
    "pl": [
        "Ta runa niesie ze sobą potężną energię transformacji. Skieruj swoją uwagę do wewnątrz i poszukaj odpowiedzi w ciszy. Starożytna mądrość prowadzi Cię na właściwą ścieżkę.",
        "Runa wskazuje na siłę ukrytą w głębi Twojej duszy. Czas na odważne decyzje i zaufanie kosmicznemu porządkowi. Przodkowie czuwają nad Tobą.",
        "Znaczenie tej runy łączy się z Twoim aktualnym stanem ducha. Otwórz się na przesłanie z wyższych sfer. Energia runiczna wspiera Twoje duchowe przebudzenie.",
    ],
    "en": [
        "This rune carries a powerful energy of transformation. Turn your attention inward and seek answers in silence. Ancient wisdom guides you along the right path.",
        "The rune points to a strength hidden deep in your soul. It is time for bold decisions and trust in the cosmic order. Your ancestors watch over you.",
        "The meaning of this rune connects with your current state of spirit. Open yourself to the message from higher realms. Runic energy supports your spiritual awakening.",
    ],
    "de": [
        "Diese Rune trägt eine mächtige Energie der Transformation in sich. Richte deine Aufmerksamkeit nach innen und suche Antworten in der Stille. Alte Weisheit führt dich auf den richtigen Weg.",
        "Die Rune weist auf eine Kraft hin, die tief in deiner Seele verborgen liegt. Es ist Zeit für mutige Entscheidungen und Vertrauen in die kosmische Ordnung. Deine Ahnen wachen über dich.",
        "Die Bedeutung dieser Rune verbindet sich mit deinem aktuellen Seelenzustand. Öffne dich für die Botschaft aus höheren Sphären. Runenenergie unterstützt dein spirituelles Erwachen.",
    ],
}

MEDITATION_THEMES: dict[str, list[str]] = {
    "pl": [
        "Wyobraź sobie, że stoisz w starożytnej świątyni otoczonej świecami. Oddychaj głęboko i poczuj jak energia Wszechświata przepływa przez Twoje ciało. Pozwól myślom odpłynąć jak liściom na jesiennym wietrze.",
        "Zamknij oczy i wyobraź sobie noc pełną gwiazd. Każda gwiazda reprezentuje jedną z Twoich wewnętrznych prawd. Wybierz jedną i pozwól jej światłu ogrzać Twoje serce.",
        "Usiądź wygodnie i zwróć uwagę na swój oddech. Wyobraź sobie strumień krystalicznie czystej wody, który obmywa Twoją duszę z napięć dnia. Z każdym oddechem czujesz się lżejszy.",
        "Poczuj pod stopami ciepłą ziemię pradawnego lasu. Drzewa szepczą starożytne mądrości do Twojego serca. Jesteś częścią wielkiego kosmicznego cyklu natury.",
        "Wyobraź sobie, że siedzisz na szczycie góry o wschodzie słońca. Ciepłe promienie budzą w Tobie ukrytą moc. Jesteś gotów na nowy dzień pełen duchowego wzrostu.",
        "Skup się na pulsowaniu swojego serca — każde uderzenie to kosmiczny rytm łączący Cię z Wszechświatem. Pozwól temu rytmowi prowadzić Twoje myśli ku wewnętrznemu spokojowi.",
        "Zamknij oczy i wyobraź sobie purpurowe światło otaczające Twoje ciało. To światło ochronne oczyszcza Twoją aurę. Oddychaj nim głęboko i poczuj wewnętrzną harmonię.",
    ],
    "en": [
        "Imagine yourself standing in an ancient temple surrounded by candles. Breathe deeply and feel the Universe's energy flowing through your body. Let your thoughts drift away like leaves on an autumn breeze.",
        "Close your eyes and picture a sky full of stars. Each star represents one of your inner truths. Choose one and let its light warm your heart.",
        "Sit comfortably and notice your breath. Imagine a stream of crystal-clear water washing your soul free of the day's tensions. With each breath you feel lighter.",
        "Feel the warm earth of a primeval forest beneath your feet. The trees whisper ancient wisdom into your heart. You are part of nature's great cosmic cycle.",
        "Imagine sitting atop a mountain at sunrise. Warm rays awaken a hidden power within you. You are ready for a new day full of spiritual growth.",
        "Focus on the beating of your heart — each pulse is a cosmic rhythm connecting you to the Universe. Let this rhythm guide your thoughts toward inner peace.",
        "Close your eyes and envision a purple light surrounding your body. This protective light purifies your aura. Breathe it in deeply and feel inner harmony.",
    ],
    "de": [
        "Stelle dir vor, du stehst in einem uralten Tempel, umgeben von Kerzen. Atme tief ein und spüre, wie die Energie des Universums durch deinen Körper fließt. Lass deine Gedanken davontreiben wie Blätter im Herbstwind.",
        "Schließe die Augen und stelle dir eine sternklare Nacht vor. Jeder Stern steht für eine deiner inneren Wahrheiten. Wähle einen und lass sein Licht dein Herz wärmen.",
        "Setze dich bequem hin und achte auf deinen Atem. Stelle dir einen Strom kristallklaren Wassers vor, der deine Seele von den Spannungen des Tages befreit. Mit jedem Atemzug fühlst du dich leichter.",
        "Spüre die warme Erde eines urzeitlichen Waldes unter deinen Füßen. Die Bäume flüstern uralte Weisheiten in dein Herz. Du bist Teil des großen kosmischen Kreislaufs der Natur.",
        "Stelle dir vor, du sitzt auf einem Berggipfel bei Sonnenaufgang. Warme Strahlen erwecken eine verborgene Kraft in dir. Du bist bereit für einen neuen Tag voller spirituellem Wachstum.",
        "Konzentriere dich auf den Schlag deines Herzens — jeder Puls ist ein kosmischer Rhythmus, der dich mit dem Universum verbindet. Lass diesen Rhythmus deine Gedanken zum inneren Frieden führen.",
        "Schließe die Augen und stelle dir ein purpurfarbenes Licht vor, das deinen Körper umgibt. Dieses Schutzlicht reinigt deine Aura. Atme es tief ein und spüre innere Harmonie.",
    ],
}


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
# Helpers
# ---------------------------------------------------------------------------
def _resolve_lang(interaction: discord.Interaction) -> str:
    locale = str(interaction.guild_locale) if interaction.guild_locale else None
    return get_user_lang(interaction.user.id, locale)


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
@tree.command(name="tarot", description="Draw a tarot card / Losuj kartę tarota 🔮")
async def cmd_tarot(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    lang = _resolve_lang(interaction)

    card_idx = random.randint(0, DECK_SIZE - 1)
    card = card_name(card_idx, lang)
    is_reversed = random.choice([True, False])
    position = t("position_reversed", lang) if is_reversed else t("position_upright", lang)

    ai_text = await ask_llm(
        system_prompt=TAROT_SYSTEM[lang].format(lang=LANG_INSTRUCTION[lang]),
        user_prompt=TAROT_USER[lang].format(card=card, position=position),
    )

    if ai_text is None:
        ai_text = random.choice(TAROT_FALLBACKS[lang])

    embed = discord.Embed(
        title=f"🃏 {card}",
        description=f"*{t('position_label', lang)}: {position}*\n\n{ai_text}\n\n{t('cta_tarot', lang)}",
        color=0x9B59B6,
    )
    embed.set_footer(text="Ezostylia • ezostylia.com")
    await interaction.followup.send(embed=embed)


@tree.command(name="runa", description="Draw a rune / Losuj runę ⚔️")
async def cmd_runa(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    lang = _resolve_lang(interaction)

    rune_idx = random.randint(0, len(ELDER_FUTHARK_I18N) - 1)
    symbol, name, kw_map = ELDER_FUTHARK_I18N[rune_idx]
    keywords = kw_map[lang]

    ai_text = await ask_llm(
        system_prompt=RUNE_SYSTEM[lang].format(lang=LANG_INSTRUCTION[lang]),
        user_prompt=RUNE_USER[lang].format(name=name, symbol=symbol, keywords=keywords),
    )

    if ai_text is None:
        ai_text = random.choice(RUNE_FALLBACKS[lang])

    embed = discord.Embed(
        title=f"{symbol} {name}",
        description=f"*{keywords}*\n\n{ai_text}\n\n{t('cta_runa', lang)}",
        color=0xE67E22,
    )
    embed.set_footer(text="Ezostylia • ezostylia.com")
    await interaction.followup.send(embed=embed)


@tree.command(name="medytacja", description="Daily meditation / Medytacja dnia 🌙")
async def cmd_medytacja(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    lang = _resolve_lang(interaction)

    seed = daily_seed()
    rng = random.Random(seed)
    theme_idx = rng.randint(0, len(MEDITATION_THEMES[lang]) - 1)

    ai_text = await ask_llm(
        system_prompt=MEDITATION_SYSTEM[lang].format(lang=LANG_INSTRUCTION[lang]),
        user_prompt=MEDITATION_USER[lang].format(date=date.today().isoformat()),
    )

    if ai_text is None:
        ai_text = MEDITATION_THEMES[lang][theme_idx]

    embed = discord.Embed(
        title=t("meditation_title", lang),
        description=f"{ai_text}\n\n{t('cta_medytacja', lang)}",
        color=0x2ECC71,
    )
    embed.set_footer(text=f"Ezostylia • {date.today().strftime('%d.%m.%Y')} • ezostylia.com")
    await interaction.followup.send(embed=embed)


@tree.command(name="language", description="Change language / Zmień język / Sprache ändern 🌐")
@app_commands.describe(lang="Language / Język / Sprache: pl, en, de")
@app_commands.choices(lang=[
    app_commands.Choice(name="🇵🇱 Polski", value="pl"),
    app_commands.Choice(name="🇬🇧 English", value="en"),
    app_commands.Choice(name="🇩🇪 Deutsch", value="de"),
])
async def cmd_language(interaction: discord.Interaction, lang: app_commands.Choice[str]):
    code = lang.value
    if code not in SUPPORTED_LANGS:
        await interaction.response.send_message(t("lang_invalid", DEFAULT_LANG), ephemeral=True)
        return
    set_user_lang(interaction.user.id, code)
    await interaction.response.send_message(t("lang_set", code), ephemeral=True)


@tree.command(name="help", description="List commands / Lista komend 📖")
async def cmd_help(interaction: discord.Interaction):
    lang = _resolve_lang(interaction)
    embed = discord.Embed(
        title=t("help_title", lang),
        description=t("help_body", lang),
        color=0x3498DB,
    )
    embed.set_footer(text=t("help_footer", lang))
    await interaction.response.send_message(embed=embed)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
