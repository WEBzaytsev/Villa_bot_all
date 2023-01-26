
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message

import keyboards
import states
from misc import dp
from orm_utils import (get_apart_prices, get_apartment, get_appart_facilities,
                       get_appart_info, get_user_apartments,
                       remove_apartment, set_apartment, toggle_listing)

# TODO: DRY

POSSIBLE_CHOICES = {'term': {
    "DAY": False,
    "MONTH": False,
    "YEAR": False,
},
    'location': {
    "CANGGU": False,
    "SEMINYAK": False,
    "ULUWATU": False,
    "UBUD": False,
    "JIMBARAN": False,
    "LAVINA": False,
    "SUKAWATI": False,
},
    'pricelist': {
    "DAY": None,
    "MONTH": None,
    "YEAR": None
},
    'bedrooms': {'1': False,
                 '2': False,
                 '3': False,
                 '4+': False, },
    'media': [],
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
                   },
}


def get_keyboard(userid, page_id: int = 1):
    text = str()
    markup = types.InlineKeyboardMarkup()
    aparts = get_user_apartments(userid=userid, page=page_id)
    if aparts:
        for count, apart in enumerate(aparts):
            if apart['shortcode']:
                prices = get_apart_prices(apart['id'])
                list_of_fac = get_appart_facilities(apart['id'])
                if list_of_fac:
                    facilities = ", ".join(list_of_fac)
                pricestext = str()
                if prices:
                    for k, v in prices.items():
                        if v:
                            pricestext += f"{k.capitalize()}: {v}\n"
                # TODO: Delisted emoji.
                text += f"""<b>{count}. Apartment {apart['shortcode']}</b>\nLocation: {apart['location']['name'].capitalize()}\nBedrooms: {apart['bedrooms']}\nFacilities: {facilities}\nPrices:\n{pricestext}"""
                # text += f"""bedrooms: {apart.bedrooms}, prices:\n"""
                # for term in statedata['term']:
                #     if not term.startswith("_"):
                #         if statedata['term'][term]:
                #             text += f'{term} price: {statedata["price"][term] if statedata["price"][term] is not None else "not set"}\n'
                markup.add(
                    types.InlineKeyboardButton(
                        f'{count}',
                        callback_data=keyboards.villalist_cb.new(id=apart['shortcode'], action='view')),
                )

        return text, markup
    return None, None


def format_request(apartid):
    appart = get_appart_info(apartid)
    if appart:
        terms = "".join(
            [f"{k.capitalize()}: {v}\n" for k, v in appart['prices'][0].items() if appart['terms'][0][k]])
        location = appart['location']['name'].capitalize()
        facilities = ", ".join([x['facility']['name'].capitalize()
                               for x in appart['facilities']])

        text = f"""
        Term and prices: \n{terms}
Location: {location}
\nBedrooms: {appart['bedrooms']}
\nFacilities: {facilities}
            """
        markup = keyboards.villa_keyboard(apartid)

        return text, markup
    return None, None


@dp.callback_query_handler(Text(equals='change_villa', ignore_case=True), state='*')
async def process_change(query: types.CallbackQuery):
    text, keyboard = get_keyboard(userid=query.from_user.id, page_id=1)

    if keyboard:
        prevbutton = types.InlineKeyboardButton(
            '⬅️ Main menu', callback_data='mainmenu')
        keyboard.add(prevbutton)
        await query.message.edit_text(text[:4096], reply_markup=keyboard, parse_mode='html')
        await states.ChangeVilla.villalist.set()
    else:
        await query.answer('Nothing added!', show_alert=True)


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='list'), state=states.ChangeVilla.villalist)
async def process_change(query: types.CallbackQuery):
    text, keyboard = get_keyboard(userid=query.from_user.id, page_id=1)
    if keyboard:
        prevbutton = types.InlineKeyboardButton(
            '⬅️ Main menu', callback_data='mainmenu')
        keyboard.add(prevbutton)
        await query.message.edit_text(text[:4096], reply_markup=keyboard, parse_mode='html')
        await states.ChangeVilla.villalist.set()
    else:
        await query.answer('Nothing added!', show_alert=True)


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='view'), state=states.ChangeVillaView.all_states)
@dp.callback_query_handler(keyboards.villalist_cb.filter(action='view'), state=states.ChangeVilla.villalist)
async def query_view(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    apartment_id = callback_data.get('id', False)

    request = get_apartment(apartment_id)
    if not request:
        return await query.answer('This villa doesnt exist!')

    await state.update_data(apartment_id=apartment_id)
    await state.update_data(apart=get_appart_info(apartment_id))

    text, markup = format_request(apartment_id)
    admin_edit = await state.get_data()
    if not admin_edit.get('admin_edit', False):
        markup.add(types.InlineKeyboardButton(
            '< Back', callback_data='change_villa'))
    if admin_edit.get('admin_edit', False):
        markup.add(types.InlineKeyboardButton(
            '< Back', callback_data='admin_menu'))
    await query.message.edit_text(text[:4096], reply_markup=markup)
    await states.ChangeVilla.villaview.set()


# @dp.message_handler(state=states.ChangeVilla.villalist)
# async def process_shortcode(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
#     id_of_villa = callback_data.get('id', False)
#     if id_of_villa:
#         text, markup = format_request(id_of_villa)
#         await query.message.edit_text(
#                 text[:4096], reply_markup=markup)
#     else:
#         await query.answer('Not found!')

@dp.callback_query_handler(Text(equals='back_pricing', ignore_case=True), state=states.Pricing.all_states)
@dp.callback_query_handler(keyboards.villalist_cb.filter(action='price'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        markup = types.InlineKeyboardMarkup()
        for k, v in statedata['apart']['prices'][0].items():
            changebutton = types.InlineKeyboardButton(
                f'{k.capitalize()}: {v}' if statedata['apart']['prices'][0][k] != None else f"{k.capitalize()}: not set", callback_data=keyboards.price_cb.new(term=k, action='change'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                '< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Current prices:", reply_markup=markup)
        await states.ChangeVillaView.changeprices.set()


@dp.callback_query_handler(keyboards.price_cb.filter(action='change'), state=states.ChangeVillaView.changeprices)
async def process_quit_price_message(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    term = query.data.split(':')[2]
    markup = types.InlineKeyboardMarkup()
    await getattr(states.ChangeVillaPricing, term.upper()).set()
    prevbutton = types.InlineKeyboardButton(
        '⬅️ Back', callback_data='back_pricing')
    markup.insert(prevbutton)

    await query.message.edit_text(f"Set price for {term}:", reply_markup=markup)


@dp.message_handler(state=states.ChangeVillaPricing.all_states)
async def process_handle_price_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    term = current_state.split(':')[1]
    price = message.text

    if message.text.isdigit():
        async with state.proxy() as statedata:
            statedata['apart']['prices'][0][term.lower()] = price
            set_apartment(
                shortcode=statedata['apartment_id'], pricelist=statedata['apart']['prices'][0])
            await message.delete()
            markup = types.InlineKeyboardMarkup()
            for k, v in statedata['apart']['prices'][0].items():

                changebutton = types.InlineKeyboardButton(
                    f'{k.capitalize()}: {v}' if statedata['apart']['prices'][0][k] != None else f"{k.capitalize()}: not set", callback_data=keyboards.price_cb.new(term=k, action='change'))
                markup.insert(changebutton)
                markup.row()
            markup.add(
                types.InlineKeyboardButton(
                    '< Back',
                    callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
            )

            await message.answer(f"{term.capitalize()} price set successful. \nCurrent prices:", reply_markup=markup)
            await states.ChangeVillaView.changeprices.set()
    else:
        return None


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='location'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        markup = types.InlineKeyboardMarkup()
        currentchoosen = statedata['apart']['location']['name']
        for k in POSSIBLE_CHOICES['location']:
            prefix = "✅ " if k == currentchoosen else ""
            changebutton = types.InlineKeyboardButton(
                f'{prefix} {k.capitalize()}', callback_data=keyboards.edit_cb.new(value=k, attrib='location'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                '< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose location:", reply_markup=markup)
        await states.ChangeVillaView.changelocation.set()


@dp.callback_query_handler(keyboards.edit_cb.filter(attrib='location'), state=states.ChangeVillaView.changelocation)
async def process_price(query: types.CallbackQuery, state: FSMContext, callback_data: dict):
    changedvalue = callback_data['value']
    async with state.proxy() as statedata:
        set_apartment(
            shortcode=statedata['apartment_id'], location=changedvalue.upper())
        statedata['apart'] = get_appart_info(statedata['apartment_id'])
        markup = types.InlineKeyboardMarkup()
        currentchoosen = statedata['apart']['location']['name']
        for k in POSSIBLE_CHOICES['location']:
            prefix = "✅ " if k == currentchoosen else ""
            changebutton = types.InlineKeyboardButton(
                f'{prefix}{k.capitalize()}', callback_data=keyboards.edit_cb.new(value=k, attrib='location'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                '< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose bedrooms:", reply_markup=markup)
        await states.ChangeVillaView.changelocation.set()
        await query.answer('Saved!')


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='bedrooms'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext, callback_data: dict):
    async with state.proxy() as statedata:
        markup = types.InlineKeyboardMarkup()
        currentchoosen = statedata['apart']['bedrooms']
        for k in POSSIBLE_CHOICES['bedrooms']:
            prefix = "✅" if int(k[0]) == currentchoosen else ""
            changebutton = types.InlineKeyboardButton(
                f'{prefix} {k.capitalize()}', callback_data=keyboards.edit_cb.new(value=k, attrib='bedrooms'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                '< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose bedrooms:", reply_markup=markup)
        await states.ChangeVillaView.changebedrooms.set()


@dp.callback_query_handler(keyboards.edit_cb.filter(attrib='bedrooms'), state=states.ChangeVillaView.changebedrooms)
async def process_price(query: types.CallbackQuery, state: FSMContext, callback_data: dict):

    changedvalue = callback_data['value'][0]

    async with state.proxy() as statedata:
        set_apartment(
            shortcode=statedata['apartment_id'], bedrooms=changedvalue)
        statedata['apart']['bedrooms'] = int(changedvalue)
        markup = types.InlineKeyboardMarkup()
        currentchoosen = statedata['apart']['bedrooms']
        for k in POSSIBLE_CHOICES['bedrooms']:
            prefix = "✅" if int(k[0]) == currentchoosen else ""
            changebutton = types.InlineKeyboardButton(
                f'{prefix} {k.capitalize()}', callback_data=keyboards.edit_cb.new(value=k, attrib='bedrooms'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                '< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose bedrooms:", reply_markup=markup)
        await states.ChangeVillaView.changebedrooms.set()
        await query.answer('Saved!')


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='facilities'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        markup = types.InlineKeyboardMarkup()
        list_of_fac = list(set(elem['facility']['name']
                           for elem in statedata['apart']['facilities']))
        for k in POSSIBLE_CHOICES['facilities']:
            prefix = "✅" if k in list_of_fac else ""
            changebutton = types.InlineKeyboardButton(
                f'{prefix} {k.capitalize()}', callback_data=keyboards.edit_cb.new(value=k, attrib='facilities'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                '< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose facilities:", reply_markup=markup)
        await states.ChangeVillaView.changefacilities.set()


@dp.callback_query_handler(keyboards.edit_cb.filter(attrib='facilities'), state=states.ChangeVillaView.changefacilities)
async def process_price(query: types.CallbackQuery, state: FSMContext, callback_data: dict):
    changedvalue = callback_data['value']

    async with state.proxy() as statedata:
        markup = types.InlineKeyboardMarkup()
        list_of_fac = list(set(elem['facility']['name']
                           for elem in statedata['apart']['facilities']))
        if changedvalue in list_of_fac:
            list_of_fac = [i for i in list_of_fac if i != changedvalue]
        else:
            list_of_fac.append(changedvalue)
        set_apartment(
            shortcode=statedata['apartment_id'], facilitylist=list_of_fac)
        await state.update_data(apart=get_appart_info(statedata['apartment_id']))

        for k in POSSIBLE_CHOICES['facilities']:
            prefix = "✅" if k in list_of_fac else ""
            changebutton = types.InlineKeyboardButton(
                f'{prefix} {k.capitalize()}', callback_data=keyboards.edit_cb.new(value=k, attrib='facilities'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                f'< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose facilities:", reply_markup=markup)
        await states.ChangeVillaView.changefacilities.set()
        await query.answer('Saved!')


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='photos'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    # TODO: CUSTOM BROWSER
    async with state.proxy() as statedata:
        await query.answer(f'Under developement')


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='toggle'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        toggle_state = toggle_listing(statedata['apartment_id'])
        if toggle_state:
            await query.answer("Listing is visible in search now!")
        else:
            await query.answer("Listing is hidden from search!")


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='remove'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        'Yes, delete', callback_data='confirm_remove'))
    async with state.proxy() as statedata:
        markup.add(
            types.InlineKeyboardButton(
                '< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )
    await query.message.edit_text("Do you want to delete this listing?", reply_markup=markup)
    await states.ChangeVillaView.confirmremove.set()


@dp.callback_query_handler(Text(equals='confirm_remove', ignore_case=True), state=states.ChangeVillaView.confirmremove)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        deletion = remove_apartment(statedata['apartment_id'])
        admin_edit = await state.get_data()
        if not admin_edit.get('admin_edit', False):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                '< Back', callback_data='change_villa'))
            await query.message.edit_text("Deleted.", reply_markup=markup)
        else:
            await query.message.edit_text("Deleted.")


@dp.callback_query_handler(keyboards.villalist_cb.filter(action='term'), state=states.ChangeVilla.villaview)
async def process_price(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        markup = types.InlineKeyboardMarkup()
        for k, v in statedata['apart']['terms'][0].items():
            changebutton = types.InlineKeyboardButton(
                f"{'✅' if v else ''} {k.capitalize()}", callback_data=keyboards.edit_cb.new(value=k, attrib='term'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                f'< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose term:", reply_markup=markup)
        await states.ChangeVillaView.changeterm.set()


@dp.callback_query_handler(keyboards.edit_cb.filter(attrib='term'), state=states.ChangeVillaView.changeterm)
async def process_price(query: types.CallbackQuery, state: FSMContext, callback_data: dict):
    changedvalue = callback_data['value']
    async with state.proxy() as statedata:
        markup = types.InlineKeyboardMarkup()
        statedata['apart']['terms'][0][changedvalue] = not statedata['apart']['terms'][0][changedvalue]
        set_apartment(
            shortcode=statedata['apartment_id'], termlist=statedata['apart']['terms'][0])
        for k, v in statedata['apart']['terms'][0].items():
            changebutton = types.InlineKeyboardButton(
                f"{'✅' if v else ''} {k.capitalize()}", callback_data=keyboards.edit_cb.new(value=k, attrib='term'))
            markup.insert(changebutton)
            markup.row()
        markup.add(
            types.InlineKeyboardButton(
                f'< Back',
                callback_data=keyboards.villalist_cb.new(id=statedata['apartment_id'], action='view')),
        )

        await query.message.edit_text("Choose term:", reply_markup=markup)
        await states.ChangeVillaView.changeterm.set()
        await query.answer('Saved!')
