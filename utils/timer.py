import asyncio
import logging
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from handlers import PremiumStates

logger = logging.getLogger(__name__)


async def start_payment_timer(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    duration: int = 300
):
    """
    Start a non-blocking countdown timer for payment.
    
    After the timer expires, prompts user to submit payment screenshot.
    
    Args:
        bot: Bot instance for sending messages
        chat_id: User's chat ID
        state: FSM context to track user state
        duration: Timer duration in seconds (default: 300 = 5 minutes)
    """
    try:
        await asyncio.sleep(duration)
        
        current_state = await state.get_state()
        if current_state != PremiumStates.timer_running.state:
            logger.info(f"Timer cancelled for user {chat_id} (state changed)")
            return
        
        await state.set_state(PremiumStates.waiting_for_screenshot)
        
        await bot.send_message(
            chat_id,
            "⏰ Time's up!\n\n"
            "If you paid then share a payment screenshot to support bot 📸\n\n"
            "Please upload your payment screenshot now."
        )
        
        logger.info(f"Timer completed for user {chat_id}")
        
    except asyncio.CancelledError:
        logger.info(f"Timer cancelled for user {chat_id}")
    except Exception as e:
        logger.error(f"Error in timer for user {chat_id}: {e}", exc_info=True)
