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

import asyncio
import aiohttp

async def health_check(request):
    return web.Response(text="OK - Lyric Card Maker Bot is Healthy", status=200)

async def keep_alive():
    await asyncio.sleep(15)  # wait for server to start up completely
    while True:
        try:
            if WEBHOOK_URL:
                health_url = f"{WEBHOOK_URL.rstrip('/')}/health"
                async with aiohttp.ClientSession() as session:
                    async with session.get(health_url) as resp:
                        print(f"Keep-alive self-ping to {health_url} -> Status {resp.status}")
        except Exception as e:
            print(f"Keep-alive self-ping exception: {e}")
        
        # Ping every 14 minutes (840 seconds) to prevent Render free instance cold start sleep
        await asyncio.sleep(840)

async def on_startup(bot: Bot):
    if WEBHOOK_URL:
        full_url = f"{WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"
        await bot.set_webhook(full_url)
        print(f"Webhook successfully set to {full_url}")
    else:
        print("Warning: WEBHOOK_URL not found. Webhook not set with Telegram.")
        
    # Start keep-alive self-ping background task
    asyncio.create_task(keep_alive())

    # Notify admin on new deploy
    admin_id = 430540319
    try:
        await bot.send_message(
            chat_id=admin_id, 
            text="🚀 Successfully deployed a new version of Lyric Card Maker Bot!"
        )
        print(f"Deploy notification sent to user {admin_id}")
    except Exception as e:
        print(f"Failed to send deploy notification: {e}")

async def on_shutdown(bot: Bot):
    print("Server shutting down...")

dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

def main():
    app = web.Application()
    
    # Health check routes for Render & UptimeRobot pings
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
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
