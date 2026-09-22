# 🌙 Ezostylia Discord Bot

Bot Discord dla społeczności Ezostylia — losuje karty tarota i runy z interpretacjami AI, prowadzi medytacje i kieruje użytkowników do ezostylia.com.

## 🚀 Szybki deploy na Render.com

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Damianwojownik/ezostylia-discord-bot)

1. Kliknij przycisk powyżej
2. Zaloguj się przez GitHub (lub utwórz darmowe konto)
3. Wpisz zmienne: `DISCORD_TOKEN` i `LLM_API_KEY`
4. Kliknij **Apply** — gotowe!

## ⚡ Komendy

| Komenda | Opis |
|---------|------|
| `/tarot` | Losuj kartę tarota z AI interpretacją |
| `/runa` | Losuj runę Elder Futhark z AI znaczeniem |
| `/medytacja` | Dzienny prompt medytacyjny |
| `/language` | Zmień język bota (pl/en/de) |
| `/help` | Lista komend |

## 🔧 Konfiguracja

### 1. Utwórz bota Discord

1. Wejdź na https://discord.com/developers/applications
2. **New Application** → nazwij "Ezostylia Bot"
3. **Bot** → **Reset Token** → skopiuj token
4. **OAuth2** → **URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Embed Links`, `Manage Channels`, `Read Message History`
5. Otwórz wygenerowany URL aby dodać bota do serwera

### 2. Zmienne środowiskowe

```
DISCORD_TOKEN=twój_token_bota
LLM_API_KEY=klucz_api
LLM_BASE_URL=https://integrations.emergentagent.com/llm/v1
LLM_MODEL=gpt-4o-mini
```

### 3. Uruchomienie lokalne

```bash
pip install -r requirements.txt
python bot.py
```

## 🔮 Funkcje

- **78 kart tarota** — pełna talia (Major + Minor Arcana) z pozycją prostą/odwróconą
- **24 runy Elder Futhark** — z symbolami unicode i słowami kluczowymi
- **AI interpretacje** — wielojęzyczne (pl/en/de)
- **Fallback offline** — działa nawet bez klucza API
- **Auto-setup kanałów** — tworzy kanały tematyczne przy dołączeniu do serwera
- **CTA do ezostylia.com** — każda odpowiedź kieruje na stronę

## ⚔️ Ezostylia
Odkryj więcej na [ezostylia.com](https://ezostylia.com)