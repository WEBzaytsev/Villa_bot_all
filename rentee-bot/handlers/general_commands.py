from os import environ

# import dateparser
import phonenumbers
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)

import keyboards
import states
from misc import Bot, bot, dp
from orm_utils import (change_pii, get_apart_prices, get_appart_facilities,
                       get_appart_media, get_saved_villa, start_user,
                       toggle_notifications)


async def get_file_as_renter_bot(file_id):
    OWNER_TOKEN = environ.get('OWNER_TOKEN')
    RENTER_BOT = Bot(token=OWNER_TOKEN)
    print(f'Trying to get {file_id}', flush=True)
    file = await RENTER_BOT.get_file(file_id)
    file_path = file.file_path
    result = await RENTER_BOT.download_file(file_path)
    return result


@dp.message_handler(commands='cancel', state='*')
@dp.message_handler(Text(equals='Cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('Canceled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state='*', commands=['start'])
@dp.message_handler(Text(equals='Main menu', ignore_case=True), state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    start_user(message.from_user.id)
    current_state = await state.get_state()  # resets state
    if current_state is not None:
        await state.finish()

    await message.answer("Welcome!", reply_markup=keyboards.main_menu)


@dp.message_handler(state=states.NewUser.name)
async def process_name(message: Message, state: FSMContext):
    sharecontact = KeyboardButton('Send contact', request_contact=True)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)\
        .add(sharecontact)

    await state.update_data(name=message.text)
    await states.NewUser.next()

    await message.reply("☎️ Please provide your telephone number:", reply_markup=markup)


@dp.message_handler(state=states.NewUser.phone, content_types=['contact'])
async def process_phone_contact(message: Message, state: FSMContext):
    phonenumber = message.contact.phone_number

    if message.contact.user_id == message.from_user.id:
        await state.update_data(phone=phonenumber)
        async with state.proxy() as data:
            change_pii(int(message.from_user.id),
                       data['name'], data['phone'])
        await message.reply(
            "👍 Profile info saved.",
            reply_markup=ReplyKeyboardRemove())
    else:
        return

    await state.finish()
    await message.answer("Welcome!", reply_markup=keyboards.main_menu)


@dp.message_handler(state=states.NewUser.phone)
async def process_phone(message: Message, state: FSMContext):
    try:
        user_number = phonenumbers.parse(message.text, 'RU')
        if not phonenumbers.is_valid_number(user_number):
            return await message.reply("🙅‍♂️ Please check your phone number. Is it entered correctly?")
    except phonenumbers.phonenumberutil.NumberParseException:
        return await message.reply("🙅‍♂️ Please check your phone number. Is it entered correctly?")

    phonenumber = phonenumbers.format_number(
        user_number, phonenumbers.PhoneNumberFormat.E164)
    await state.update_data(phone=phonenumber)
    async with state.proxy() as data:
        change_pii(int(message.from_user.id),
                   data['name'], data['phone'])
    await message.reply(
        "👍 Profile info saved.",
        reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await message.answer("Welcome!", reply_markup=keyboards.main_menu)


@dp.callback_query_handler(Text(equals='change_pii', ignore_case=True))
async def process_change_pii(query: types.CallbackQuery):
    await query.answer()
    await query.message.answer("Please enter your name:", reply_markup=ReplyKeyboardRemove())
    await states.NewUser.name.set()


@dp.callback_query_handler(Text(equals='toggle_notification', ignore_case=True))
async def process_toggle_notifications(query: types.CallbackQuery):
    toggle_state = toggle_notifications(query.from_user.id)
    if toggle_state:
        await query.answer("You will receive notifications from now.")
    else:
        await query.answer("You will not receive any notifications.")


@dp.callback_query_handler(Text(equals='show_saved_villa', ignore_case=True))
async def process_get_saved_villa(query: types.CallbackQuery):
    list_of_aparts = get_saved_villa(query.from_user.id)
    if list_of_aparts:
        for apart in list_of_aparts:
            if apart.get('shortcode', None):
                medialen = 0
                media = types.MediaGroup()
                media_list = get_appart_media(apart['apartment'])
                prices = get_apart_prices(apart['apartment'])
                facilities = ", ".join(
                    get_appart_facilities(apart['apartment']))
                pricestext = str()
                for k, v in prices.items():
                    pricestext += f"{k}: {v}\n"
                text = f"""Bedrooms: {apart['bedrooms']}\nLocation: {apart['location']}\nShortcode: {apart['shortcode']}\nFacilities: {facilities}\nPrices:\n{pricestext}"""
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
                        file = await get_file_as_renter_bot(photo['file_id'])
                        media.attach_photo(file)

                    msg_photos = await query.message.reply_media_group(media)
                    await msg_photos[0].reply(text, reply_markup=keyboards.contact_keyboard(apart['shortcode']))
    else:
        await query.message.answer("Nothing found!")
