# 🌙 Ezostylia Discord Bot

Bot Discord dla społeczności Ezostylia — losuje karty tarota i runy z interpretacjami AI, prowadzi medytacje i kieruje użytkowników do ezostylia.com.

## ⚡ Komendy

| Komenda | Opis |
|---------|------|
| `/tarot` | Losuj kartę tarota z AI interpretacją |
| `/runa` | Losuj runę Elder Futhark z AI znaczeniem |
| `/medytacja` | Dzienny prompt medytacyjny |
| `/help` | Lista komend |

## 🔧 Jak skonfigurować

### 1. Utwórz bota Discord

1. Wejdź na https://discord.com/developers/applications
2. Kliknij **New Application** → nazwij np. "Ezostylia Bot"
3. Przejdź do **Bot** → **Reset Token** → skopiuj token
4. Włącz w **Bot**:
   - `SERVER MEMBERS INTENT` — OFF (niepotrzebne)
   - `MESSAGE CONTENT INTENT` — OFF (niepotrzebne)
5. Przejdź do **OAuth2** → **URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Manage Channels`, `Read Message History`
6. Skopiuj wygenerowany URL i otwórz go w przeglądarce aby dodać bota do serwera

### 2. Zmienne środowiskowe

```
DISCORD_TOKEN=twój_token_bota
LLM_API_KEY=klucz_api_emergent
LLM_BASE_URL=https://integrations.emergentagent.com/llm/v1
LLM_MODEL=gpt-4o-mini
```

### 3. Uruchomienie lokalne

```bash
pip install -r requirements.txt
export DISCORD_TOKEN="..."
export LLM_API_KEY="..."
python bot.py
```

### 4. Deploy na Render.com (darmowy tier)

1. Wrzuć kod na GitHub
2. Na render.com → **New** → **Blueprint** → połącz z repo
3. Render automatycznie przeczyta `render.yaml`
4. Ustaw zmienne środowiskowe `DISCORD_TOKEN` i `LLM_API_KEY`
5. Deploy!

**Uwaga:** Darmowy tier Render usypia worker po 15 min bezczynności. Bot wróci online po następnym evencie.

## 📂 Struktura plików

```
discord-bot/
├── bot.py              # Główny plik bota
├── requirements.txt    # Zależności Python
├── render.yaml         # Konfiguracja Render.com
└── README.md           # Ten plik
```

## 🔮 Funkcje

- **78 kart tarota** — pełna talia (Major + Minor Arcana) z pozycją prostą/odwróconą
- **24 runy Elder Futhark** — z symbolami unicode i słowami kluczowymi
- **AI interpretacje** — OpenAI-compatible API w języku polskim
- **Fallback offline** — działa nawet bez klucza API (predefiniowane interpretacje)
- **Auto-setup kanałów** — tworzy kanały tematyczne przy dołączeniu do serwera
- **CTA do ezostylia.com** — każda odpowiedź kieruje na stronę

## ⚔️ Ezostylia
Odkryj więcej na [ezostylia.com](https://ezostylia.com)
