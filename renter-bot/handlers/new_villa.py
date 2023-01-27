from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, MediaGroup, Message)
from aiogram.utils.exceptions import BadRequest
from aiogram_calendar import (SimpleCalendar, simple_cal_callback)

import keyboards
import states
from misc import bot, dp
from orm_utils import new_apartment, set_apartment_media, is_admin

from .general_commands import cmd_start_alt

# import dateparser
# import phonenumbers


DEFAULT_DATA = {'term': {
    "DAY": False,
    "MONTH": False,
    "YEAR": False,
    "_multiple": True,
},
    'location': {
    "CANGGU": False,
    "SEMINYAK": False,
    "ULUWATU": False,
    "UBUD": False,
    "JIMBARAN": False,
    "LAVINA": False,
    "SUKAWATI": False,
    "_multiple": False,
},
    'price': {
    "DAY": None,
    "MONTH": None,
    "YEAR": None
},
    'bedrooms': {'1': False,
                 '2': False,
                 '3': False,
                 '4+': False,
                 "_multiple": False},
    'media': [],
    'checkindate': None,
    'facilities': {'PRIVATEPOOL': False,
                   'SHAREDPOOL': False,
                   'BATHTUBE': False,
                   'KITCHEN': False,
                   'CLEANING': False,
                   'WIFI': False,
                   'AC': False,
                   'LAUNDRY': False,
                   'DISHWASHER': False,
                   'PETFRIENDLY': False,
                   "_multiple": True,
                   },
}

"""
TODO: DEFAULT_DATA = {'term': {
        "_multiple": True,
    },
        'location': {
        "_multiple": False,
    },
        'price': {
    },
        'bedrooms': {},
        'media': [],
        'facilities': {
                    "_multiple": True,
                    },
        
    }

dynamically get info from db
"""


def _keyboard(state, statedata, toggledbutton=None):
    markup = InlineKeyboardMarkup()

    if statedata:
        if toggledbutton:
            if statedata[state]["_multiple"]:
                statedata[state][toggledbutton] = not statedata[state][toggledbutton]
            else:
                for button in statedata[state]:
                    if toggledbutton == button:
                        statedata[state][toggledbutton] = not statedata[state][toggledbutton]
                    else:
                        statedata[state][button] = False

        for button in statedata[state]:
            if button.startswith("_") or state in ["media", "price"]:
                continue
            if statedata[state][button]:
                prefix = "✅"
            else:
                prefix = ""

            markup.add(
                InlineKeyboardButton(
                    f'{prefix} {button.capitalize()}',
                    callback_data=keyboards.choicer_cb.new(state=state, button=button)),
            )
        markup.row()
        # TODO: wouldn't be better to get elements from state class? check https://github.com/aiogram/aiogram/blob/df294e579f104e2ae7e9f37b0c69490782d33091/aiogram/dispatcher/filters/state.py
        if state == 'price':
            for term in statedata['term']:
                if not term.startswith("_"):
                    if statedata['term'][term]:
                        changebutton = InlineKeyboardButton(
                            f'{term} price: {statedata["price"][term] if statedata["price"][term] is not None else "not set"}', callback_data=keyboards.price_cb.new(term=term, action='change'))
                        markup.insert(changebutton)
                        markup.row()
        if list(statedata.keys())[0] != state:
            prevbutton = InlineKeyboardButton(
                '⬅️ Back', callback_data=keyboards.pager_cb.new(state=state, button='prev'))
            markup.insert(prevbutton)
        if list(statedata.keys())[0] == state:
            prevbutton = InlineKeyboardButton(
                '⬅️ Back', callback_data='mainmenu')
            markup.insert(prevbutton)
        if list(statedata.keys())[:-1] != state:
            nextbutton = InlineKeyboardButton(
                '➡️ Next', callback_data=keyboards.pager_cb.new(state=state, button='next'))
            markup.insert(nextbutton)
        # TODO: parse and add statedata to database, finish state, congratulate user (?) and return to main menu.
        return markup
    return None


# @dp.message_handler(commands=['new'], state='*')
# @dp.message_handler(Text(equals='🏠 Add villa', ignore_case=True))
@dp.callback_query_handler(Text(equals='add_villa', ignore_case=True))
async def process_term(query: CallbackQuery, state: FSMContext):
    await state.update_data(data=DEFAULT_DATA)

    async with state.proxy() as statedata:
        markup = _keyboard('term', statedata)
        statedata['initial_message'] = query.message.message_id

    await query.answer()
    await query.message.edit_text("Terms:", reply_markup=markup)
    await states.NewVilla.term.set()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.location)
async def process_term(query: CallbackQuery, state: FSMContext):
    await query.answer()

    async with state.proxy() as statedata:
        markup = _keyboard('term', statedata)

    await query.message.edit_text("Term:", reply_markup=markup)
    await states.NewVilla.term.set()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.term)
@dp.callback_query_handler(Text(equals='mainmenu', ignore_case=True), state='*')
async def process_mainmenu(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await state.finish()
    markup = keyboards.main_menu()
    if is_admin(query.from_user.id):
        markup = keyboards.main_menu(admin=True)
    return await query.message.edit_text("Welcome!", reply_markup=markup)
    


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.term)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.pricing)
async def process_location(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if [key for key, value in statedata['term'].items() if value and key != "_multiple"]:
            await query.answer()
            markup = _keyboard('location', statedata)

            await query.message.edit_text("Location:", reply_markup=markup)
            await states.NewVilla.location.set()
        else:
            await query.answer(
                text='Nothing selected.', show_alert=True)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.facilities)
async def process_bedrooms(query: CallbackQuery, state: FSMContext):
    await query.answer()

    async with state.proxy() as statedata:
        markup = _keyboard('bedrooms', statedata)

    await query.message.edit_text("Bedrooms:", reply_markup=markup)
    await states.NewVilla.bedrooms.set()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.pricing)
async def process_bedrooms(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if [key for key, value in statedata['price'].items() if value and key != "_multiple" and statedata['term'][key] == bool(value)]:
            await query.answer()

            markup = _keyboard('bedrooms', statedata)

            await query.message.edit_text("Bedrooms:", reply_markup=markup)
            await states.NewVilla.bedrooms.set()
        else:
            await query.answer(
                text='Please enter prices for all chosen terms!', show_alert=True)


@dp.callback_query_handler(Text(startswith="toggle"), state=states.NewVilla.all_states)
async def process_toggle_callback(query: CallbackQuery, state: FSMContext):
    await query.answer()

    test = await state.get_state()
    test = test.split(':')
    test2 = query.data.split(':')
    async with state.proxy() as statedata:
        markup = _keyboard(test[1], statedata, test2[2])

    await query.message.edit_text(query.message.text, reply_markup=markup)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.facilities)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.checkindate)
async def process_media(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if [key for key, value in statedata['facilities'].items() if value and key != "_multiple"]:
            await query.answer()

            async with state.proxy() as statedata:
                markup = _keyboard('media', statedata)

            await query.message.edit_text("Send a picture for listing:", reply_markup=markup)
            await states.NewVilla.media.set()
        else:
            await query.answer(
                text='Nothing selected.', show_alert=True)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.checkindate)
async def process_preview(query: CallbackQuery, state: FSMContext):
    await query.answer()
    async with state.proxy() as statedata:
        terms = ", ".join(
            key for key, value in statedata['term'].items() if value and key != "_multiple")
        location = ", ".join(key for key, value in statedata['location'].items(
        ) if value and key != "_multiple")
        facilities = ", ".join(key for key, value in statedata['facilities'].items(
        ) if value and key != "_multiple")
        bedrooms = "".join(key for key, value in statedata['bedrooms'].items(
        ) if value and key != "_multiple")[0]
        markup = InlineKeyboardMarkup()
        prevbutton = InlineKeyboardButton(
            '⬅️ Back', callback_data=keyboards.pager_cb.new(state='facilities', button='prev'))
        addbutton = InlineKeyboardButton(
            '🔼 Add', callback_data=keyboards.pager_cb.new(state='preview', button='finish'))
        markup.insert(prevbutton)
        markup.insert(addbutton)
        medialen = len(statedata["media"])
        text = f"""Term: {terms}
Location: {location}
Facilities: {facilities}
Bedrooms: {bedrooms}
Prices:\n"""
        for term in statedata['term']:
            if not term.startswith("_"):
                if statedata['term'][term]:
                    text += f'{term} price: {statedata["price"][term] if statedata["price"][term] is not None else "not set"}\n'

        if medialen:
            if medialen == 1:
                await query.message.reply_photo(statedata["media"][0], text, reply_markup=markup)
            if medialen >= 2:
                for media in statedata["media"]:
                    media = MediaGroup()
                    media_list = statedata["media"]

                    for i, photo in enumerate(media_list):
                        if i == 0:
                            media.attach_photo(photo, caption=text)
                        else:
                            media.attach_photo(photo)

                msg_photos = await query.message.reply_media_group(media)
                await msg_photos[0].reply(text, reply_markup=markup)
        else:
            await query.message.edit_text(text=text, reply_markup=markup)
        await states.NewVilla.preview.set()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='finish'), state=states.NewVilla.preview)
async def process_finish(query: CallbackQuery, state: FSMContext):
    await query.answer()

    async with state.proxy() as statedata:
        terms = ", ".join(
            key for key, value in statedata['term'].items() if value and key != "_multiple")
        location = "".join(key for key, value in statedata['location'].items(
        ) if value and key != "_multiple")
        facilities = ", ".join(key for key, value in statedata['facilities'].items(
        ) if value and key != "_multiple")
        bedrooms = "".join(key for key, value in statedata['bedrooms'].items(
        ) if value and key != "_multiple")[0]
        markup = InlineKeyboardMarkup()
        prevbutton = InlineKeyboardButton(
            '⬅️ Main menu', callback_data='mainmenu')
        markup.insert(prevbutton)
        apart = new_apartment(tgid=query.from_user.id,
                              bedrooms=int(bedrooms),
                              location=location,
                              facilitylist=[
                                  key for key, value in statedata['facilities'].items() if value and key != "_multiple"],
                              pricelist=statedata['price'])
        await query.message.reply("Done!", reply_markup=markup)
        await query.message.delete()

        for photo in statedata["media"]:
            set_apartment_media(apart, photo)
    await state.finish()
    await cmd_start_alt(message=query.message, state=state)


@dp.message_handler(content_types='photo', state=states.NewVilla.media)
async def process_message_photo(message: Message, state: FSMContext):
    # TODO: cancel photo add
    markup = InlineKeyboardMarkup()
    nextbutton = InlineKeyboardButton(
        'Continue', callback_data=keyboards.pager_cb.new(state='media', button='next'))
    markup.insert(nextbutton)
    async with state.proxy() as statedata:
        medialen = len(statedata['media'])
        if 10 > medialen:
            statedata['media'].append(message.photo[-1].file_id)
            await message.delete()
            await bot.edit_message_text('Added! Send more photos or click "Continue" if you have finished adding photos.', message.from_user.id, statedata['initial_message'], reply_markup=markup)
        elif medialen == 10:
            await message.delete()
            await bot.edit_message_text("You have added the maximum number of photos - please click Continue.", message.from_user.id, statedata['initial_message'], reply_markup=markup)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.bedrooms)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.media)
async def process_facilities(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if [key for key, value in statedata['bedrooms'].items() if value and key != "_multiple"]:
            await query.answer()

            async with state.proxy() as statedata:
                markup = _keyboard('facilities', statedata)

            await query.message.edit_text("Facilities:", reply_markup=markup)
            await states.NewVilla.facilities.set()
        else:
            await query.answer(
                text='Nothing selected.', show_alert=True)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.location)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.bedrooms)
@dp.callback_query_handler(Text(equals='back_pricing', ignore_case=True), state=states.Pricing.all_states)
async def process_price(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if [key for key, value in statedata['location'].items() if value and key != "_multiple"]:
            await query.answer()

            async with state.proxy() as statedata:
                markup = _keyboard('price', statedata)

            await query.message.edit_text("Prices:", reply_markup=markup)
            await states.NewVilla.pricing.set()
        else:
            await query.answer(
                text='Nothing selected.', show_alert=True)


@dp.callback_query_handler(keyboards.price_cb.filter(action='change'), state=states.NewVilla.pricing)
async def process_quit_price_message(query: CallbackQuery, state: FSMContext):
    await query.answer()
    term = query.data.split(':')[2]
    markup = InlineKeyboardMarkup()
    await getattr(states.Pricing, term).set()
    prevbutton = InlineKeyboardButton(
        '⬅️ Back', callback_data='back_pricing')
    markup.insert(prevbutton)

    await query.message.edit_text(f"Set price for {term}:", reply_markup=markup)


@dp.message_handler(state=states.Pricing.all_states)
async def process_handle_price_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    term = current_state.split(':')[1]
    price = message.text

    if message.text.isdigit():
        async with state.proxy() as statedata:
            statedata['price'][term] = price
            markup = _keyboard('price', statedata)
            await message.delete()
            await bot.edit_message_text(f"{term} price set successful. \nCurrent prices:", chat_id=message.from_id, message_id=statedata['initial_message'], reply_markup=markup)
            await states.NewVilla.pricing.set()
    else:
        return None


@dp.callback_query_handler(simple_cal_callback.filter(), state=states.NewVilla.checkindate)
async def process_simple_calendar(query: CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as statedata:
        if callback_data:  # and callback_data
            selected, date = await SimpleCalendar().process_selection(query, callback_data)
            statedata['checkindate'] = date
        else:
            selected, date = (False, statedata['checkindate'])
        markup = InlineKeyboardMarkup()\
            .add(InlineKeyboardButton(
                '👍 Yes, continue.', callback_data=keyboards.pager_cb.new(state='checkindate', button='next')))\
            .add(InlineKeyboardButton(
                '👎 No, correct it.', callback_data=keyboards.pager_cb.new(state='checkindate', button='reset')))
        if selected:
            await bot.edit_message_text(f'You selected {date.strftime("%d/%m/%Y")}. Is this the right date?', query.from_user.id, statedata['initial_message'], reply_markup=markup)
        if not selected and statedata['checkindate']:
            # TODO: sometimes acts weird
            await query.message.delete()
            await states.NewVilla.checkindate.set()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.media)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.preview)
async def process_checkindate(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if statedata['media']:
            if not statedata['checkindate']:
                await query.answer()

                markup = await SimpleCalendar().start_calendar()
                markup.row()
                prevbutton = InlineKeyboardButton(
                    '⬅️ Back', callback_data=keyboards.pager_cb.new(state='checkindate', button='prev'))
                markup.insert(prevbutton)
                nextbutton = InlineKeyboardButton(
                    '➡️ Next', callback_data=keyboards.pager_cb.new(state='checkindate', button='next'))
                markup.insert(nextbutton)

                await states.NewVilla.checkindate.set()
                try:
                    await query.message.edit_text("Select check-in date:", reply_markup=markup)
                except BadRequest:
                    await query.message.delete()
                    await bot.edit_message_text("Select check-in date:", query.from_user.id, statedata['initial_message'], reply_markup=markup)
            else:
                await process_simple_calendar(query, None, state=state)
        else:
            await query.answer(
                text='Please add at least one photo.', show_alert=True)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='reset'), state=states.NewVilla.checkindate)
async def process_checkindate_reset(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if statedata['media']:

            await state.update_data(checkindate=None)
            await process_checkindate(query, state)
        else:
            await query.answer(
                text='Please add at least one photo.', show_alert=True)


# let manage added photos

# no correct doesnt work
# cant go back from calendar
# TypeError: list indices must be integers or slices, not str
