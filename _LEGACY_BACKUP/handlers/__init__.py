from aiogram.fsm.state import State, StatesGroup

class PremiumStates(StatesGroup):
    waiting_for_plan_selection = State()
    viewing_qr = State()
    timer_running = State()
    waiting_for_screenshot = State()
    waiting_for_email = State()
    pending_approval = State()
