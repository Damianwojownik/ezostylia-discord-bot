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
