from aiogram.fsm.state import State, StatesGroup


class Waiting(StatesGroup):
    feedback = State()
    group = State()
    notify_time = State()

    dist = State()
    setup_group = State()
