"""
Friday Bazar Payments Bot
==========================
Main entry point with aiohttp health server + aiogram polling
Deployment: Render Free Tier (Web Service)
"""

import asyncio
import logging
import sys
import warnings
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

# Fix for Windows SSL warnings
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Suppress SSL warnings
    warnings.filterwarnings('ignore', category=ResourceWarning)

from src.config import BOT_TOKEN, WEBAPP_HOST, WEBAPP_PORT, ADMIN_IDS
from src.services.db import db
from src.handlers import catalog, payment, referrals, admin, misc, user, language, support, moderation, menu_admin, dashboard, custom_buttons, admin_qr, admin_pricing, admin_system, admin_features
from src.middlewares.language import LanguageMiddleware
from src.middlewares.antispam import AntiSpamMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.MARKDOWN
)

# Initialize dispatcher
dp = Dispatcher()

# Register middlewares (language and anti-spam for all messages)
dp.message.middleware(LanguageMiddleware())
dp.callback_query.middleware(LanguageMiddleware())
dp.message.middleware(AntiSpamMiddleware(rate_limit=10, time_window=60))

# Register routers (order matters - most specific first)
    # Include routers
dp.include_router(dashboard.router)
dp.include_router(admin_features.router) # Consolidated features
dp.include_router(admin_system.router)
dp.include_router(admin_pricing.router)
dp.include_router(admin_qr.router)
dp.include_router(language.router)
dp.include_router(menu_admin.router)
dp.include_router(admin.router)
dp.include_router(catalog.router)
dp.include_router(payment.router)
dp.include_router(referrals.router)
dp.include_router(support.router)
dp.include_router(user.router) # User commands
dp.include_router(custom_buttons.router)
dp.include_router(moderation.router)
dp.include_router(misc.router)

# Health check endpoint for Render
async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="OK", status=200)

async def root_handler(request):
    """Root endpoint with bot info"""
    return web.Response(
        text="🤖 Friday Bazar Payments Bot is running!\n\nVisit @FridayBazarBot on Telegram",
        status=200
    )

async def on_startup():
    """Run on bot startup with cache warming"""
    logger.info("[STARTUP] Starting Friday Bazar Payments Bot...")
    
    # Initialize database
    await db.initialize()
    logger.info("[OK] Database initialized")

    # Initialize settings and services
    from src.services.settings import settings_manager
    await settings_manager.initialize()
    logger.info("[OK] Settings & Services initialized")
    
    # Warm up service cache
    try:
        from src.services.cache import service_cache
        from src.data.services import get_all_services
        
        services = get_all_services()
        # Pre-load all services into cache
        for service_id, service_data in services.items():
            await service_cache.set(f"service_{service_id}", service_data)
        
        logger.info(f"[OK] Service cache warmed ({len(services)} services)")
    except Exception as e:
        logger.warning(f"[WARN] Could not warm service cache: {e}")
    
    # Set up bot commands menu
    from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
    
    # Commands for regular users
    user_commands = [
        BotCommand(command="start", description="🎉 Start the bot / Welcome"),
        BotCommand(command="language", description="🌐 Change language (EN/HI/BN)"),
        BotCommand(command="help", description="🆘 Get help and FAQ"),
        BotCommand(command="status", description="📊 Check subscription & coins"),
        BotCommand(command="support", description="📞 Contact support"),
        BotCommand(command="cancel", description="❌ Cancel current operation"),
    ]
    
    # Set commands for all users (default scope)
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    logger.info("[OK] User command menu set (6 commands)")
    
    # Admin commands (extended list)
    admin_commands = [
        BotCommand(command="start", description="🎉 Start the bot"),
        BotCommand(command="dashboard", description="🎛️ Admin Dashboard (NEW!)"),
        BotCommand(command="admin", description="👨‍💼 Admin panel info"),
        BotCommand(command="language", description="🌐 Change language"),
        BotCommand(command="help", description="🆘 Get help"),
        BotCommand(command="status", description="📊 Check status"),
        BotCommand(command="support", description="📞 Support"),
        BotCommand(command="menu_add", description="➕ Add menu button"),
        BotCommand(command="menu_remove", description="➖ Remove menu button"),
        BotCommand(command="menu_list", description="📋 List menu buttons"),
        BotCommand(command="mod_keyword_add", description="🔑 Add keyword reply"),
        BotCommand(command="mod_keyword_remove", description="🗑️ Remove keyword"),
        BotCommand(command="mod_keyword_list", description="📜 List keywords"),
    ]
    
    # Set admin commands for each admin
    for admin_id in ADMIN_IDS:
        try:
            await bot.set_my_commands(
                admin_commands, 
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.warning(f"Could not set admin commands for {admin_id}: {e}")
    
    logger.info(f"[OK] Admin command menu set for {len(ADMIN_IDS)} admin(s) (12 commands)")
    
    # Start polling
    logger.info("[OK] Bot polling started - optimized and ready!")

async def on_shutdown():
    """Run on bot shutdown"""
    logger.info("[SHUTDOWN] Shutting down bot...")
    try:
        await db.shutdown() # Force save data
        await bot.session.close()
        await asyncio.sleep(0.25)  # Give time for connections to close
    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")
    logger.info("[SHUTDOWN] Cleanup complete")

async def main():
    """Main function to run bot and web server concurrently"""
    
    # Initialize on startup
    await on_startup()
    
    # Create aiohttp app for health checks
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', root_handler)
    
    # Create web server runner
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    
    # Start web server
    await site.start()
    logger.info(f"[WEB] Server started on {WEBAPP_HOST}:{WEBAPP_PORT}")
    
    try:
        # Start bot polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
