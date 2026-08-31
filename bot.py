import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from handlers import router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app-name.onrender.com
PORT = int(os.getenv("PORT", 10000))    # Render provides the PORT env variable
WEBHOOK_PATH = "/webhook"

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found.")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def on_startup(bot: Bot):
    if WEBHOOK_URL:
        full_url = f"{WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"
        await bot.set_webhook(full_url)
        print(f"Webhook successfully set to {full_url}")
    else:
        print("Warning: WEBHOOK_URL not found. Webhook not set with Telegram.")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)

dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

def main():
    app = web.Application()
    
    # Handle incoming webhook requests
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Tie dispatcher startup/shutdown to the web app
    setup_application(app, dp, bot=bot)
    
    print(f"Starting web application on 0.0.0.0:{PORT}...")
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
