from aiogram.dispatcher.filters.state import State, StatesGroup


class NewUser(StatesGroup):
    name = State()
    phone = State()


class Menu(StatesGroup):
    main = State()
    change_personal_info = State()
    # appointments = State() # TODO: target
    # listed_villas = State() # WIP


class NewVilla(StatesGroup):
    term = State()
    location = State()
    price = State()
    bedrooms = State()
    facilities = State()
    # checkindate = State()
    preview = State()


class Pricing(StatesGroup):
    MIN = State()
    MAX = State()
