import asyncio
import logging
from os import environ

from aiogram import Bot, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message
from aiogram.utils import exceptions

import keyboards
import states
from misc import bot, dp
from orm_utils import get_custom_user_searches, is_admin

from .admin_menu import admin_menu

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

RENTEE_TOKEN = environ.get('RENTEE_TOKEN')
bot_rentee = Bot(token=RENTEE_TOKEN)


DEFAULT_DATA = {'term': {
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
    "SUKAWATI": False, },
    'price': {"till 1m": False,
              "1 - 3 m": False,
              "3 - 5 m": False,
              "> 5 m": False,
              "till 20 m": False,
              "20 - 30 m": False,
              "30 - 40 m": False,
              ">40 m": False,
              "till 150 m": False,
              "150 - 250 m": False,
              "250 - 400 m": False,
              ">400 m": False,
              },
    'bedrooms': {'1': False,
                 '2': False,
                 '3': False,
                 '4+': False, },
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


def _keyboard(state, statedata, toggledbutton=None):
    markup = types.InlineKeyboardMarkup()

    if toggledbutton:
        # if isinstance(statedata[state][toggledbutton], None):
        if statedata[state][toggledbutton] is None:
            pass
        else:
            for button in statedata[state]:
                if toggledbutton == button:
                    statedata[state][toggledbutton] = not statedata[state][toggledbutton]

    for button in statedata[state]:
        if statedata[state][button]:
            prefix = "✅"
        else:
            prefix = ""

        markup.add(
            types.InlineKeyboardButton(
                f'{prefix} {button.capitalize()}',
                callback_data=keyboards.choicer_cb.new(state=state, button=button)),
        )

    markup.row()
    prevbutton = types.InlineKeyboardButton(
        '⬅️ Back', callback_data='admin_broadcast')
    markup.insert(prevbutton)
    return markup


def _text(statedata):
    broadcast_text = statedata.get("broadcast_text", "not_specified")
    result = {}
    for part in ('price', 'term', 'location', 'bedrooms'):
        part_values = [key for key, value in statedata[part].items() if value]
        result[part] = part_values if part_values else "not specified"
    text = f"""
🎯 Targeting:
Price: {result['price']}
Terms: {result['term']}
Location: {result['location']}
Bedrooms: {result['bedrooms']}

Text: {broadcast_text}
"""
    return text


def _get_all_recipients(statedata, count=False):
    result = {}
    for part in ('price', 'term', 'location', 'bedrooms'):
        part_values = [key for key, value in statedata[part].items() if value]
        result[part] = part_values if part_values else "not specified"
    broadcast_facilities = []
    if count:
        recipients = get_custom_user_searches(
            facility_list=broadcast_facilities,
            location_list=result['location'],
            term_list=result['term'],
            bedrooms_list=result['bedrooms'],
            price_list=result['price'],
            count=True)
    else:
        recipients = get_custom_user_searches(
            facility_list=broadcast_facilities,
            location_list=result['location'],
            term_list=result['term'],
            bedrooms_list=result['bedrooms'],
            price_list=result['price'])
    return recipients


async def send_message(user_id: int, text: str, disable_notification: bool = False):
    try:
        await bot_rentee.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcaster(users_list, text):
    count = 0
    try:
        for user_id in users_list:
            if await send_message(user_id, text):
                count += 1
            # await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
            # 20 messages per second (Limit: 30 messages per second)
            await asyncio.sleep(.15)
    finally:
        log.info(f"{count} messages successful sent.")

    return count


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='admin_broadcast', ignore_case=True), state=states.Menu.admin_menu)
async def admin_broadcast_from_admin(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(data=DEFAULT_DATA)
    await state.update_data(broadcast_text=None)
    await admin_broadcast(query, state)


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='admin_broadcast', ignore_case=True), state=states.BroadcastState.all_states)
async def admin_broadcast(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        # await query.answer(f'Under developement')

        keyboard = keyboards.broadcast_keyboard()
        async with state.proxy() as statedata:
            text = _text(statedata)
            recipients = _get_all_recipients(statedata, True)
            text += f"\nCount of recipients: {recipients}"
        if keyboard:
            prevbutton = types.InlineKeyboardButton(
                '⬅️ Back', callback_data='admin_menu')
            keyboard.add(prevbutton)
            await query.message.edit_text(f'{text}', reply_markup=keyboard)
            await states.BroadcastState.change.set()


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='change_text', ignore_case=True), state=states.BroadcastState.change)
async def change_text(query: types.CallbackQuery, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    prevbutton = types.InlineKeyboardButton(
        '⬅️ Back', callback_data='admin_broadcast')
    keyboard.add(prevbutton)
    await query.message.edit_text('Send text:', reply_markup=keyboard)
    await states.BroadcastState.changetext.set()


@dp.message_handler(lambda c: is_admin(c.from_user.id), state=states.BroadcastState.changetext)
async def process_changetext_message(message: Message, state: FSMContext):
    keyboard = keyboards.broadcast_keyboard()
    prevbutton = types.InlineKeyboardButton(
        '⬅️ Back', callback_data='admin_menu')
    keyboard.add(prevbutton)
    async with state.proxy() as statedata:
        recipients = _get_all_recipients(statedata)
        statedata['broadcast_text'] = message.text
        text = _text(statedata)
        text += f"\nCount of recipients: {recipients}"
        await bot.edit_message_text(f'Saved!\n{text}', message.from_user.id, statedata['initial_message'], reply_markup=keyboard)
    await message.delete()
    await states.BroadcastState.change.set()


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='target_price', ignore_case=True), state=states.BroadcastState.change)
async def target_price(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        keyboard = _keyboard('price', statedata)
    await states.BroadcastState.price.set()
    await query.message.edit_text('Target prices:', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='target_terms', ignore_case=True), state=states.BroadcastState.change)
async def target_terms(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        keyboard = _keyboard('term', statedata)
    await states.BroadcastState.term.set()
    await query.message.edit_text('Target terms:', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='target_location', ignore_case=True), state=states.BroadcastState.change)
async def target_location(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        keyboard = _keyboard('location', statedata)
    await states.BroadcastState.location.set()
    await query.message.edit_text('Target location:', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='target_bedrooms', ignore_case=True), state=states.BroadcastState.change)
async def target_bedrooms(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        keyboard = _keyboard('bedrooms', statedata)
    await states.BroadcastState.bedrooms.set()
    await query.message.edit_text('Target bedrooms:', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='send_broadcast', ignore_case=True), state=states.BroadcastState.change)
async def send_broadcast(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        recipients = _get_all_recipients(statedata, True)
    if recipients:
        keyboard = types.InlineKeyboardMarkup()
        confirm = types.InlineKeyboardButton(
            'Confirm', callback_data='send_broadcast_confirm')
        keyboard.add(confirm)
        prevbutton = types.InlineKeyboardButton(
            '⬅️ Back', callback_data='admin_broadcast')
        keyboard.add(prevbutton)

        await states.BroadcastState.confirmsend.set()
        async with state.proxy() as statedata:
            text = _text(statedata)
        await query.message.edit_text(f'Confirm sending:\n\n{text}', reply_markup=keyboard)
    else:
        await query.answer('No recipients.', show_alert=True)


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='send_broadcast_confirm', ignore_case=True), state=states.BroadcastState.confirmsend)
async def send_broadcast_confirm(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as statedata:
        recipients = _get_all_recipients(statedata)
        text = statedata['broadcast_text']
    asyncio.create_task(broadcaster(recipients, text))
    await query.answer('Broadcast queued successfully.', show_alert=True)
    await admin_menu(query=query, state=state)


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(startswith="toggle"), state=states.BroadcastState.all_states)
async def process_toggle_callback(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    test = await state.get_state()
    test = test.split(':')
    test2 = query.data.split(':')
    async with state.proxy() as statedata:
        markup = _keyboard(test[1], statedata, test2[2])

    await query.message.edit_text(query.message.text, reply_markup=markup)
