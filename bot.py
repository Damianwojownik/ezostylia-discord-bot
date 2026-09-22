import json
import os
import pathlib
import asyncio
import threading
from collections import deque
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import discord
from discord import app_commands
from openai import AsyncOpenAI

# ---------------------------------------------------------------------
# Config (environment variables)
# ---------------------------------------------------------------------
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
LLM_API_KEY   = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("Llm_BASE_URL", "https://integrations.emergentagent.net/llm")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.0-flash")

# ---------------------------------------------------------------------
# Twitter / X integration
# ---------------------------------------------------------------------
TTWITTERE_API_KEY        = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET     = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN   = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "")

# Runtime toggle - can be flipped by admin commands without restart
_twitter_enabled: bool = bool(
    TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET
)

# Simple daily rate limit: max 10 tweets per day
_tweet_timestamps: deque = deque()
TWEET_DAILY_LIMIT = 10

def _can_tweet() -> bool:
    """Return True if under the daily tweet limit."""
    now = datetime.utcnow()
    # Remove timestamps older than 24h
    while _tweet_timestamps and (now - _tweet_timestamps[0]).total_seconds() > 86400:
        _tweet_timestamps.popleft()
    return len(_tweet_timestamps) < TWEET_DAILY_LIMIT

def _record_tweet() -> None:
    _tweet_timestamps.append(datetime.utcnow())

async def post_to_twitter(text: str) -> None:
    """Post a tweet asynchronously. Silently skips if disabled or over limit."""
    if not _twitter_enabled:
        return
    if not _can_tweet():
        print("[TWITTER] Daily tweet limit reached, skipping.")
        return
    try:
        import tweepy
        loop = asyncio.get_event_loop()
        def _post():
            client = tweepy.Client(
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_SECRET,
            )
            client.create_tweet(text=text)
        await loop.run_in_executor(None, _post)
        _record_tweet()
        print(f"[TWITTER] Tweet posted: {text[:60]}...")
    except ImportError:
        print("[TWITTER] tweepy not installed, skipping.")
    except Exception as exc:
        print(f"[TWITTER] Error posting tweet: {exc}")
