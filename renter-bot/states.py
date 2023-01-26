from aiogram.dispatcher.filters.state import State, StatesGroup


class NewUser(StatesGroup):
    name = State()
    phone = State()


class Menu(StatesGroup):
    main = State()
    change_personal_info = State()
    # appointments = State() # TODO: target
    listed_villas = State()  # TODO: target
    admin_menu = State()
    admin_edit = State()


class NewVilla(StatesGroup):
    """
    term -> location -> pricing  -> bedrooms -> facilities -> media -> checkindate -> preview
    """
    term = State()
    location = State()
    pricing = State()
    bedrooms = State()
    facilities = State()
    media = State()
    checkindate = State()
    preview = State()


class Pricing(StatesGroup):
    DAY = State()
    MONTH = State()
    YEAR = State()


class ChangeVilla(StatesGroup):
    villalist = State()
    villaview = State()
    villaview_admin = State()


class ChangeVillaView(StatesGroup):
    change = State()
    changeprices = State()
    changeprices_setting = State()
    changeterm = State()
    changelocation = State()
    changebedrooms = State()
    changefacilities = State()
    changephotos = State()
    changephotos_upload = State()
    confirmremove = State()


class ChangeVillaPricing(StatesGroup):
    DAY = State()
    MONTH = State()
    YEAR = State()


class BroadcastState(StatesGroup):
    change = State()
    changetext = State()
    price = State()
    term = State()
    location = State()
    bedrooms = State()
    changefacilities = State()
    confirmsend = State()
