Python 3.12.8 (tags/v3.12.8:2dc476b, Dec  3 2024, 19:30:04) [MSC v.1942 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

# Initial setup
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# In-memory cache
class CryptoCache:
    def __init__(self):
        self.data = []
        self.last_updated = None

cache = CryptoCache()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_crypto_data():
    """Fetch crypto data from API with auto-retry"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                os.getenv("API_URL", "https://api.coingecko.com/api/v3/coins/markets"),
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 10,
                    "page": 1,
                    "sparkline": "false"
                },
                headers={"User-Agent": "CryptoBot/2.0"},
                timeout=15
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise

async def update_cache():
    """Update cache every 10 minutes"""
    try:
        data = await fetch_crypto_data()
        if data and isinstance(data, list):
            cache.data = data
            cache.last_updated = datetime.now()
            logger.info("✅ Cache updated at %s", cache.last_updated)
    except Exception as e:
        logger.error(f"❌ Cache update failed: {e}")

def format_price(price: float) -> str:
    """Professional price formatting"""
    return "${:,.2f}".format(price) if price >= 0.01 else "${:,.4f}".format(price)

async def send_report():
    """Generate and send report"""
    try:
        if not cache.data:
            await update_cache()

        bot = Bot(token=os.getenv("7764154158:AAE6ZHnmyF2xdyF2DYX9Rf33GXl0fAfWwVg"))
        message = "🔥 **Top 10 Cryptocurrencies Report** 📊\n\n"
        
        for idx, coin in enumerate(cache.data, 1):
            change_24h = coin.get('price_change_percentage_24h', 0)
            change_emoji = "📈🟢" if change_24h >= 0 else "📉🔴"
            
            message += (
                f"{idx}. **{coin['name']} ({coin['symbol'].upper()})**\n"
                f"   💵 Price: {format_price(coin['current_price'])}, \n"
                f"   {change_emoji} 24h Change: {abs(change_24h):.2f}%\n"
                f"   🌍 Market Cap: ${coin['market_cap']:,.0f}\n\n"
            )

        message += f"_Last Updated: {cache.last_updated.strftime('%Y-%m-%d %H:%M:%S UTC')}_"
        
        await bot.send_message(
            chat_id=os.getenv("https://t.me/trcplan"),
...             text=message,
...             parse_mode="Markdown",
...             disable_web_page_preview=True
...         )
...         logger.info("📤 Report sent successfully!")
...     except TelegramError as e:
...         logger.error(f"Telegram Error: {e}")
...     except Exception as e:
...         logger.error(f"Critical Error: {e}")
... 
... async def main():
...     """Main execution"""
...     scheduler = AsyncIOScheduler()
...     
...     # Scheduling
...     scheduler.add_job(
...         send_report,
...         trigger="interval",
...         hours=4,
...         max_instances=1
...     )
...     
...     scheduler.add_job(
...         update_cache,
...         trigger="interval",
...         minutes=10,
...         max_instances=1
...     )
...     
...     scheduler.start()
...     
...     # Initial execution
...     await update_cache()
...     await send_report()
...     
...     # Infinite execution
...     await asyncio.Future()
... 
... if __name__ == "__main__":
