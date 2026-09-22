"""Tests for Ezostylia Discord Bot (with tri-lingual i18n support)."""
import hashlib
import os
import sys
import json
import tempfile
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set required env vars before importing bot
os.environ["DISCORD_TOKEN"] = "test-token-fake"
os.environ["LLM_API_KEY"] = ""
# Use a temp file for prefs so tests don't pollute the real one
_prefs_tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
_prefs_tmp.close()
os.environ["PREFS_PATH"] = _prefs_tmp.name

import bot


# ---------------------------------------------------------------------------
# Tarot deck tests
# ---------------------------------------------------------------------------
class TestTarotDeck:
    def test_major_arcana_count(self):
        assert len(bot.MAJOR_ARCANA) == 22

    def test_minor_arcana_count(self):
        assert len(bot.MINOR_ARCANA) == 56

    def test_full_deck_count(self):
        assert len(bot.FULL_DECK) == 78
        assert bot.DECK_SIZE == 78

    def test_no_duplicate_cards(self):
        assert len(set(bot.FULL_DECK)) == 78

    def test_minor_arcana_suits(self):
        for suit in bot.SUITS:
            cards_in_suit = [c for c in bot.MINOR_ARCANA if suit in c]
            assert len(cards_in_suit) == 14, f"Suit {suit} has {len(cards_in_suit)} cards"

    def test_minor_arcana_ranks(self):
        for suit in bot.SUITS:
            for rank in bot.RANKS:
                card = f"{rank} {suit}"
                assert card in bot.MINOR_ARCANA, f"Missing card: {card}"

    def test_major_arcana_i18n_count(self):
        assert len(bot.MAJOR_ARCANA_I18N) == 22

    def test_major_arcana_i18n_languages(self):
        for entry in bot.MAJOR_ARCANA_I18N:
            for lang in ("pl", "en", "de"):
                assert lang in entry, f"Missing lang {lang} in {entry}"


# ---------------------------------------------------------------------------
# card_name tests
# ---------------------------------------------------------------------------
class TestCardName:
    def test_major_arcana_pl(self):
        assert bot.card_name(0, "pl") == "G\u0142upiec"

    def test_major_arcana_en(self):
        assert bot.card_name(0, "en") == "The Fool"

    def test_major_arcana_de(self):
        assert bot.card_name(0, "de") == "Der Narr"

    def test_minor_arcana_first(self):
        # Index 22 = first minor card = Ace of Wands
        assert bot.card_name(22, "en") == "Ace Wands"

    def test_minor_arcana_pl(self):
        assert bot.card_name(22, "pl") == "As Bu\u0142awy"

    def test_last_card(self):
        # Index 77 = last card = King of Pentacles
        assert bot.card_name(77, "en") == "King Pentacles"


# ---------------------------------------------------------------------------
# Rune tests
# ---------------------------------------------------------------------------
class TestRunes:
    def test_elder_futhark_count(self):
        assert len(bot.ELDER_FUTHARK) == 24

    def test_elder_futhark_i18n_count(self):
        assert len(bot.ELDER_FUTHARK_I18N) == 24

    def test_rune_structure(self):
        for rune in bot.ELDER_FUTHARK:
            assert len(rune) == 3
            symbol, name, keywords = rune
            assert len(symbol) >= 1
            assert len(name) >= 2
            assert len(keywords) >= 5

    def test_rune_i18n_languages(self):
        for symbol, name, kw_map in bot.ELDER_FUTHARK_I18N:
            for lang in ("pl", "en", "de"):
                assert lang in kw_map, f"Missing lang {lang} for rune {name}"

    def test_unique_rune_names(self):
        names = [r[1] for r in bot.ELDER_FUTHARK]
        assert len(set(names)) == 24

    def test_unique_rune_symbols(self):
        symbols = [r[0] for r in bot.ELDER_FUTHARK]
        assert len(set(symbols)) == 24


# ---------------------------------------------------------------------------
# Auto-channels tests
# ---------------------------------------------------------------------------
class TestAutoChannels:
    def test_channel_count(self):
        assert len(bot.AUTO_CHANNELS) == 7

    def test_witaj_present(self):
        assert "witaj" in bot.AUTO_CHANNELS


# ---------------------------------------------------------------------------
# Welcome message tests
# ---------------------------------------------------------------------------
class TestWelcomeMessage:
    def test_contains_commands(self):
        assert "/tarot" in bot.WELCOME_MESSAGE
        assert "/runa" in bot.WELCOME_MESSAGE
        assert "/medytacja" in bot.WELCOME_MESSAGE
        assert "/language" in bot.WELCOME_MESSAGE

    def test_contains_website(self):
        assert "ezostylia.com" in bot.WELCOME_MESSAGE


# ---------------------------------------------------------------------------
# I18N / CTA tests
# ---------------------------------------------------------------------------
class TestI18N:
    def test_cta_tarot_all_langs(self):
        for lang in ("pl", "en", "de"):
            assert "ezostylia.com" in bot.t("cta_tarot", lang)

    def test_cta_runa_all_langs(self):
        for lang in ("pl", "en", "de"):
            assert "ezostylia.com" in bot.t("cta_runa", lang)

    def test_cta_medytacja_all_langs(self):
        for lang in ("pl", "en", "de"):
            assert "ezostylia.com" in bot.t("cta_medytacja", lang)

    def test_t_fallback_to_pl(self):
        # Unknown lang falls back to pl (DEFAULT_LANG)
        result = bot.t("cta_tarot", "xx")
        assert result == bot.I18N["cta_tarot"]["pl"]

    def test_t_unknown_key(self):
        result = bot.t("nonexistent_key", "pl")
        assert result == "nonexistent_key"

    def test_lang_set_messages(self):
        assert "polski" in bot.t("lang_set", "pl").lower()
        assert "english" in bot.t("lang_set", "en").lower()
        assert "deutsch" in bot.t("lang_set", "de").lower()

    def test_help_body_all_langs(self):
        for lang in ("pl", "en", "de"):
            body = bot.t("help_body", lang)
            assert "/tarot" in body
            assert "/runa" in body
            assert "/medytacja" in body
            assert "/language" in body

    def test_position_labels(self):
        assert bot.t("position_upright", "pl") == "prosta"
        assert bot.t("position_upright", "en") == "upright"
        assert bot.t("position_reversed", "de") == "umgekehrt"


# ---------------------------------------------------------------------------
# Language detection / preferences
# ---------------------------------------------------------------------------
class TestLanguagePrefs:
    def setup_method(self):
        bot._user_lang_prefs.clear()

    def test_detect_lang_from_locale_pl(self):
        assert bot.detect_lang_from_locale("pl") == "pl"

    def test_detect_lang_from_locale_en(self):
        assert bot.detect_lang_from_locale("en-US") == "en"
        assert bot.detect_lang_from_locale("en-GB") == "en"

    def test_detect_lang_from_locale_de(self):
        assert bot.detect_lang_from_locale("de") == "de"
        assert bot.detect_lang_from_locale("de-DE") == "de"

    def test_detect_lang_from_locale_unknown(self):
        assert bot.detect_lang_from_locale("fr") == bot.DEFAULT_LANG

    def test_detect_lang_from_locale_none(self):
        assert bot.detect_lang_from_locale(None) == bot.DEFAULT_LANG

    def test_set_and_get_user_lang(self):
        bot.set_user_lang(12345, "de")
        assert bot.get_user_lang(12345) == "de"

    def test_get_user_lang_falls_back_to_locale(self):
        # No explicit pref -> use guild locale
        assert bot.get_user_lang(99999, "en-US") == "en"

    def test_user_pref_overrides_locale(self):
        bot.set_user_lang(42, "de")
        assert bot.get_user_lang(42, "en-US") == "de"

    def test_prefs_persistence(self):
        bot.set_user_lang(100, "en")
        # Read the prefs file
        data = json.loads(bot.PREFS_PATH.read_text())
        assert data["100"] == "en"


# ---------------------------------------------------------------------------
# Daily seed tests
# ---------------------------------------------------------------------------
class TestDailySeed:
    def test_seed_deterministic(self):
        s1 = bot.daily_seed()
        s2 = bot.daily_seed()
        assert s1 == s2

    def test_seed_is_int(self):
        assert isinstance(bot.daily_seed(), int)

    def test_seed_positive(self):
        assert bot.daily_seed() > 0


# ---------------------------------------------------------------------------
# Fallback content tests (now dicts keyed by language)
# ---------------------------------------------------------------------------
class TestFallbacks:
    def test_tarot_fallbacks_all_langs(self):
        for lang in ("pl", "en", "de"):
            assert len(bot.TAROT_FALLBACKS[lang]) >= 3

    def test_rune_fallbacks_all_langs(self):
        for lang in ("pl", "en", "de"):
            assert len(bot.RUNE_FALLBACKS[lang]) >= 3

    def test_meditation_themes_all_langs(self):
        for lang in ("pl", "en", "de"):
            assert len(bot.MEDITATION_THEMES[lang]) >= 7

    def test_polish_fallbacks_contain_polish(self):
        polish_chars = set("\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c\u0104\u0106\u0118\u0141\u0143\u00d3\u015a\u0179\u017b")
        for text in bot.TAROT_FALLBACKS["pl"] + bot.RUNE_FALLBACKS["pl"] + bot.MEDITATION_THEMES["pl"]:
            has_polish = any(c in polish_chars for c in text)
            assert has_polish, f"Not Polish: {text[:50]}..."

    def test_german_fallbacks_contain_german(self):
        german_chars = set("\u00e4\u00f6\u00fc\u00df\u00c4\u00d6\u00dc")
        all_de = bot.TAROT_FALLBACKS["de"] + bot.RUNE_FALLBACKS["de"] + bot.MEDITATION_THEMES["de"]
        has_any_german = any(any(c in german_chars for c in text) for text in all_de)
        assert has_any_german, "No German-specific characters in DE fallbacks"


# ---------------------------------------------------------------------------
# LLM client tests
# ---------------------------------------------------------------------------
class TestLLMClient:
    def test_no_client_without_key(self):
        bot.llm_client = None
        original = bot.LLM_API_KEY
        bot.LLM_API_KEY = ""
        client = bot.get_llm_client()
        assert client is None
        bot.LLM_API_KEY = original

    def test_client_created_with_key(self):
        bot.llm_client = None
        original = bot.LLM_API_KEY
        bot.LLM_API_KEY = "test-key-123"
        client = bot.get_llm_client()
        assert client is not None
        bot.LLM_API_KEY = original
        bot.llm_client = None


# ---------------------------------------------------------------------------
# ask_llm tests
# ---------------------------------------------------------------------------
class TestAskLLM:
    @pytest.mark.asyncio
    async def test_returns_none_without_key(self):
        bot.llm_client = None
        original = bot.LLM_API_KEY
        bot.LLM_API_KEY = ""
        result = await bot.ask_llm("system", "user")
        assert result is None
        bot.LLM_API_KEY = original

    @pytest.mark.asyncio
    async def test_returns_text_on_success(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Moc tarota jest z Tob\u0105."

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        bot.llm_client = mock_client
        original = bot.LLM_API_KEY
        bot.LLM_API_KEY = "test-key"

        result = await bot.ask_llm("system prompt", "user prompt")
        assert result == "Moc tarota jest z Tob\u0105."

        bot.LLM_API_KEY = original
        bot.llm_client = None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        bot.llm_client = mock_client
        original = bot.LLM_API_KEY
        bot.LLM_API_KEY = "test-key"

        result = await bot.ask_llm("system prompt", "user prompt")
        assert result is None

        bot.LLM_API_KEY = original
        bot.llm_client = None


# ---------------------------------------------------------------------------
# Config validation tests
# ---------------------------------------------------------------------------
class TestConfig:
    def test_llm_base_url(self):
        assert "emergentagent.com" in bot.LLM_BASE_URL

    def test_llm_model(self):
        assert bot.LLM_MODEL == "gpt-4o-mini"

    def test_discord_token_from_env(self):
        assert bot.DISCORD_TOKEN == "test-token-fake"

    def test_supported_langs(self):
        assert bot.SUPPORTED_LANGS == ("pl", "en", "de")

    def test_default_lang(self):
        assert bot.DEFAULT_LANG == "pl"


# ---------------------------------------------------------------------------
# Meditation date-seed consistency
# ---------------------------------------------------------------------------
class TestMeditationSeed:
    def test_same_day_same_theme(self):
        import random
        seed = bot.daily_seed()
        for lang in ("pl", "en", "de"):
            rng1 = random.Random(seed)
            idx1 = rng1.randint(0, len(bot.MEDITATION_THEMES[lang]) - 1)
            rng2 = random.Random(seed)
            idx2 = rng2.randint(0, len(bot.MEDITATION_THEMES[lang]) - 1)
            assert idx1 == idx2


# ---------------------------------------------------------------------------
# LLM prompt templates
# ---------------------------------------------------------------------------
class TestLLMPrompts:
    def test_tarot_system_all_langs(self):
        for lang in ("pl", "en", "de"):
            prompt = bot.TAROT_SYSTEM[lang].format(lang=bot.LANG_INSTRUCTION[lang])
            assert len(prompt) > 20

    def test_rune_system_all_langs(self):
        for lang in ("pl", "en", "de"):
            prompt = bot.RUNE_SYSTEM[lang].format(lang=bot.LANG_INSTRUCTION[lang])
            assert len(prompt) > 20

    def test_meditation_system_all_langs(self):
        for lang in ("pl", "en", "de"):
            prompt = bot.MEDITATION_SYSTEM[lang].format(lang=bot.LANG_INSTRUCTION[lang])
            assert len(prompt) > 20

    def test_tarot_user_template(self):
        for lang in ("pl", "en", "de"):
            prompt = bot.TAROT_USER[lang].format(card="The Fool", position="upright")
            assert "The Fool" in prompt

    def test_rune_user_template(self):
        for lang in ("pl", "en", "de"):
            prompt = bot.RUNE_USER[lang].format(name="Fehu", symbol="\u16a0", keywords="Wealth")
            assert "Fehu" in prompt

    def test_meditation_user_template(self):
        for lang in ("pl", "en", "de"):
            prompt = bot.MEDITATION_USER[lang].format(date="2026-01-01")
            assert "2026-01-01" in prompt


# ---------------------------------------------------------------------------
# Guild join event tests
# ---------------------------------------------------------------------------
class TestGuildJoin:
    @pytest.mark.asyncio
    async def test_creates_missing_channels(self):
        guild = AsyncMock()
        guild.text_channels = []

        created_channels = {}

        async def mock_create(name):
            ch = AsyncMock()
            ch.name = name
            created_channels[name] = ch
            return ch

        guild.create_text_channel = mock_create

        await bot.on_guild_join(guild)

        for ch_name in bot.AUTO_CHANNELS:
            assert ch_name in created_channels, f"Channel {ch_name} was not created"

    @pytest.mark.asyncio
    async def test_skips_existing_channels(self):
        existing = []
        for name in bot.AUTO_CHANNELS:
            ch = AsyncMock()
            ch.name = name
            existing.append(ch)

        guild = AsyncMock()
        guild.text_channels = existing

        create_mock = AsyncMock()
        guild.create_text_channel = create_mock

        with patch("bot.discord.utils.get", return_value=existing[0]):
            await bot.on_guild_join(guild)

        create_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_sends_welcome_in_witaj(self):
        guild = AsyncMock()
        guild.text_channels = []

        witaj_ch = AsyncMock()
        witaj_ch.name = "witaj"

        async def mock_create(name):
            if name == "witaj":
                return witaj_ch
            ch = AsyncMock()
            ch.name = name
            return ch

        guild.create_text_channel = mock_create

        await bot.on_guild_join(guild)

        witaj_ch.send.assert_called_once_with(bot.WELCOME_MESSAGE)
