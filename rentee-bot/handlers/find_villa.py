from os import environ

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, MediaGroup, Message)

import keyboards
import states
from misc import Bot, bot, dp
from orm_utils import (add_to_favorite, get_apart_prices, get_apartment,
                       get_appart, get_appart_facilities, get_appart_media,
                       set_custom_user_search)

from .general_commands import cmd_start

# import dateparser
# import phonenumbers

PRICE_RANGES = {
    "DAY": {"till 1m": False,
            "1 - 3 m": False,
            "3 - 5 m": False,
            "> 5 m": False, },
    "MONTH": {"till 20 m": False,
              "20 - 30 m": False,
              "30 - 40 m": False,
              ">40 m": False, },
    "YEAR": {"till 150 m": False,
             "150 - 250 m": False,
             "250 - 400 m": False,
             ">400 m": False, }}

DEFAULT_DATA = {'term': {
    "DAY": False,
    "MONTH": False,
    "YEAR": False,
    "_multiple": False,
},
    'location': {
    "CANGGU": False,
    "SEMINYAK": False,
    "ULUWATU": False,
    "UBUD": False,
    "JIMBARAN": False,
    "LAVINA": False,
    "SUKAWATI": False,
    "_multiple": True,
},
    'price': {
    "_multiple": False,
},
    'bedrooms': {'1': False,
                 '2': False,
                 '3': False,
                 '4+': False,
                 "_multiple": True},
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


def _keyboard(state, statedata, toggledbutton=None):
    markup = InlineKeyboardMarkup()

    if statedata:
        if state == 'price':
            term_str = "".join(
                key for key, value in statedata['term'].items() if value and key != "_multiple")

            statedata_def = DEFAULT_DATA['price'].copy()

            statedata_def.update(PRICE_RANGES[term_str])
            if set(statedata_def) != set(statedata['price']):
                statedata['price'] = statedata_def
        if toggledbutton:
            # if isinstance(statedata[state][toggledbutton], None):
            if statedata[state][toggledbutton] is None:
                pass
            elif statedata[state]["_multiple"]:
                statedata[state][toggledbutton] = not statedata[state][toggledbutton]
            else:
                for button in statedata[state]:
                    if toggledbutton == button:
                        statedata[state][toggledbutton] = not statedata[state][toggledbutton]
                    else:
                        statedata[state][button] = False

        for button in statedata[state]:
            if statedata[state][button]:
                prefix = "✅"
            else:
                prefix = ""
            if button.startswith("_") or state in ["media"]:
                continue

            markup.add(
                InlineKeyboardButton(
                    f'{prefix} {button.capitalize()}',
                    callback_data=keyboards.choicer_cb.new(state=state, button=button)),
            )

        markup.row()
        # if state == 'price':

        # for price in statedata['price']:
        #     changebutton = InlineKeyboardButton(
        #         f'{price}: {statedata["price"][price] if statedata["price"][price] != None else "not set"}', callback_data=keyboards.price_cb.new(term=price, action='change'))
        #     markup.insert(changebutton)
        #     markup.row()
        # TODO: wouldn't be better to get elements from state class? check https://github.com/aiogram/aiogram/blob/df294e579f104e2ae7e9f37b0c69490782d33091/aiogram/dispatcher/filters/state.py

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
        return markup
    return None

OWNER_TOKEN = environ.get('OWNER_TOKEN')
RENTER_BOT = Bot(token=OWNER_TOKEN)
async def get_file_as_renter_bot(file_id):
    print(f'Trying to get {file_id}', flush=True)
    file = await RENTER_BOT.get_file(file_id)
    file_path = file.file_path
    result = await RENTER_BOT.download_file(file_path)
    return result


# @dp.message_handler(commands=['search'], state='*')
@dp.callback_query_handler(Text(equals='find_villa', ignore_case=True))
async def find_villa(query: CallbackQuery, state: FSMContext):
    await state.update_data(data=DEFAULT_DATA)

    async with state.proxy() as statedata:
        markup = _keyboard('term', statedata)
        statedata['initial_message'] = query.message.message_id

    await query.answer()
    await query.message.edit_text("Term:", reply_markup=markup)
    await states.NewVilla.term.set()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.term)
@dp.callback_query_handler(Text(equals='mainmenu', ignore_case=True), state='*')
async def process_mainmenu(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.edit_text("Welcome!", reply_markup=keyboards.main_menu)
    await state.finish()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.term)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.price)
async def process_location(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        if [key for key, value in statedata['term'].items() if value and key != "_multiple"]:
            markup = _keyboard('location', statedata)

            await query.message.edit_text("Location:", reply_markup=markup)
            await states.NewVilla.location.set()
        else:
            await query.answer(
                text='Nothing selected.', show_alert=True)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.location)
async def process_term(query: CallbackQuery, state: FSMContext):
    await query.answer()

    async with state.proxy() as statedata:
        markup = _keyboard('term', statedata)

    await query.message.edit_text("Term:", reply_markup=markup)
    await states.NewVilla.term.set()


@dp.callback_query_handler(Text(startswith="toggle"), state='*')
async def process_toggle_callback(query: CallbackQuery, state: FSMContext):
    await query.answer()
    test = await state.get_state()
    test = test.split(':')
    test2 = query.data.split(':')
    async with state.proxy() as statedata:
        markup = _keyboard(test[1], statedata, test2[2])

    await query.message.edit_text(query.message.text, reply_markup=markup)


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.bedrooms)
# @dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.facilities)
async def process_preview(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        text = str()
        terms = ", ".join(
            key for key, value in statedata['term'].items() if value and key != "_multiple")
        location = ", ".join(key for key, value in statedata['location'].items(
        ) if value and key != "_multiple")
        price = ", ".join(key for key, value in statedata['price'].items(
        ) if value and key != "_multiple")
        facilities = ", ".join(key for key, value in statedata['facilities'].items(
        ) if value and key != "_multiple")

        text += f"Term: {terms}\n" if terms != ", " else "Term: not chosen\n"
        text += f"Price: {price}" if price != ", " else "Price: not chosen\n"
        text += f"Location: {location}" if location != ", " else "Location: not chosen\n"
        # text += f"Facilities: {facilities}" if facilities != ", " else None

        markup = InlineKeyboardMarkup()
        prevbutton = InlineKeyboardButton(
            '⬅️ Back', callback_data=keyboards.pager_cb.new(state='facilities', button='prev'))
        searchbutton = InlineKeyboardButton(
            '🔎 Search', callback_data=keyboards.pager_cb.new(state='preview', button='finish'))
        markup.insert(prevbutton)
        markup.insert(searchbutton)
        await query.message.edit_text(text, reply_markup=markup)
        await states.NewVilla.preview.set()
    await query.answer()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='finish'), state=states.NewVilla.preview)
async def search_send(query: CallbackQuery, state: FSMContext):
    await query.answer()
    async with state.proxy() as statedata:
        markup = InlineKeyboardMarkup()
        prevbutton = InlineKeyboardButton(
            '⬅️ Back', callback_data=keyboards.pager_cb.new(state='facilities', button='prev'))
        markup.insert(prevbutton)
        await query.message.edit_text("Searching...")
    await state.finish()

    facilities_list = [key for key, value in statedata['facilities'].items(
    ) if value and key != "_multiple"]
    locations_list = [key for key, value in statedata['location'].items(
    ) if value and key != "_multiple"]
    term_str = "".join(
        key for key, value in statedata['term'].items() if value and key != "_multiple")
    price_str = "".join(
        key for key, value in statedata['price'].items() if value and key != "_multiple")
    bedroom_list = [key[0] for key, value in statedata['bedrooms'].items(
    ) if value and key != "_multiple"]

    list_of_aparts = get_appart(
        facility_list=facilities_list,
        location_list=locations_list,
        term=term_str,
        price=price_str,
        bedrooms=bedroom_list)

    set_custom_user_search(tgid=query.from_user.id,
                           facility_list=facilities_list,
                           location_list=locations_list,
                           term_list=[term_str],
                           price_list=[price_str],
                           bedrooms_list=bedroom_list,
                           )

    if list_of_aparts:
        for apart in list_of_aparts:
            if apart['shortcode']:
                medialen = 0
                media = MediaGroup()
                media_list = get_appart_media(apart['id'])
                price = get_apart_prices(apart['id'], term_str)
                list_of_fac = get_appart_facilities(apart['id'])
                if list_of_fac:
                    facilities = ", ".join(list_of_fac)

                text = str()
                if apart['bedrooms']:
                    text += f"""Bedrooms: {apart['bedrooms']}\n"""

                text += f"""Appartment {apart['shortcode']}\nLocation: {apart['location']['name']}\nPrice: {price}\n """
                if list_of_fac:
                    text += f"""\nFacilities: {facilities}"""
                if media_list:
                    medialen = len(media_list)
                    if medialen == 0:
                        await query.message.reply(
                            text, reply_markup=keyboards.contact_keyboard(apart['shortcode']))
                    if medialen == 1:
                        file = await get_file_as_renter_bot(media_list[0]['file_id'])
                        await query.message.reply_photo(file, text, reply_markup=keyboards.contact_keyboard(apart['shortcode']))
                    else:
                        for photo in media_list:
                            # FIXME: laggy, use channels
                            file = await get_file_as_renter_bot(photo['file_id'])
                            media.attach_photo(file)

                        msg_photos = await query.message.reply_media_group(media)
                        await msg_photos[0].reply(text, reply_markup=keyboards.contact_keyboard(apart['shortcode']))
    else:
        await query.message.answer("Nothing found!")
    await cmd_start(message=query.message, state=state)


# @dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.bedrooms)
# @dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.preview)
# async def process_facilities(query: CallbackQuery, state: FSMContext):
#     await query.answer()

#     async with state.proxy() as statedata:
#         markup = _keyboard('facilities', statedata)

#     await query.message.edit_text("Facilities:", reply_markup=markup)
#     await states.NewVilla.facilities.set()


# @dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.price)
# @dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.facilities)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.price)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.preview)
async def process_bedrooms(query: CallbackQuery, state: FSMContext):
    await query.answer()

    async with state.proxy() as statedata:
        markup = _keyboard('bedrooms', statedata)

    await query.message.edit_text("Bedrooms:", reply_markup=markup)
    await states.NewVilla.bedrooms.set()


@dp.callback_query_handler(keyboards.pager_cb.filter(button='next'), state=states.NewVilla.location)
@dp.callback_query_handler(keyboards.pager_cb.filter(button='prev'), state=states.NewVilla.bedrooms)
@dp.callback_query_handler(Text(equals='back_pricing', ignore_case=True), state=states.Pricing.all_states)
async def process_price(query: CallbackQuery, state: FSMContext):
    await query.answer()

    async with state.proxy() as statedata:
        markup = _keyboard('price', statedata)

    await query.message.edit_text("Prices range:", reply_markup=markup)
    await states.NewVilla.price.set()


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
            await bot.edit_message_text(f"{term} price set successful. \nCurrent prices range:", chat_id=message.from_id, message_id=statedata['initial_message'], reply_markup=markup)
            await states.NewVilla.price.set()
    else:
        return None


@dp.callback_query_handler(keyboards.price_cb.filter(action='change'), state=states.NewVilla.price)
async def process_quit_price_message(query: CallbackQuery):
    await query.answer()
    term = query.data.split(':')[2]
    markup = InlineKeyboardMarkup()
    await getattr(states.Pricing, term).set()
    prevbutton = InlineKeyboardButton(
        '⬅️ Back', callback_data='back_pricing')
    markup.insert(prevbutton)

    await query.message.edit_text(f"Set price for {term}:", reply_markup=markup)


@dp.callback_query_handler(keyboards.villaaction.filter(action='contact'), state='*')
async def process_contact(query: CallbackQuery):
    await query.answer()
    # TODO: Paywall
    shortcode = query.data.split(':')[1]
    apartment = get_apartment(shortcode)
    if not apartment.external:
        markup = InlineKeyboardMarkup()\
            .add(InlineKeyboardButton("🟢 Open WhatsApp", url=f"https://wa.me/{apartment.user.phone}"))
        await query.message.reply(f"👤 Name: {apartment.user.name}\n☎️ Phone: +{apartment.user.phone}\nUnique shortcode: {apartment.shortcode}", reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()\
            .add(InlineKeyboardButton("🟢 Open WhatsApp", url=f"https://wa.me/{apartment.phone}"))
        await query.message.reply(f"👤 Name: {apartment.author}\n☎️ Phone: +{apartment.phone}\nUnique shortcode: {apartment.shortcode}", reply_markup=markup)


@dp.callback_query_handler(keyboards.villaaction.filter(action='save'), state='*')
async def process_favorite(query: CallbackQuery):
    # TODO: get markup and change button via await query.message.edit_reply_markup()
    shortcode = query.data.split(':')[1]
    added = add_to_favorite(query.from_user.id, shortcode)
    if added:
        await query.answer("Saved!")
    else:
        await query.answer("Removed from saved!")
