import phonenumbers
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)

import keyboards
import states
from misc import dp
from orm_utils import change_pii, start_user, is_admin, is_admin_exists, switch_admin


async def cmd_start_alt(message: types.Message, state: FSMContext):
    current_state = await state.get_state()  # resets state
    if current_state is not None:
        await state.finish()
    markup = keyboards.main_menu()
    if is_admin(message.from_user.id):
        markup = keyboards.main_menu(admin=True)
    return await message.answer("Welcome!", reply_markup=markup)


@dp.message_handler(state='*', commands=['start'])
@dp.message_handler(Text(equals='Main menu', ignore_case=True), state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    new_user = start_user(message.from_user.id)

    if new_user:
        await message.answer(f"Hello, {message.from_user.first_name}! Please enter your name:", reply_markup=ReplyKeyboardRemove())
        await states.NewUser.name.set()
    else:
        current_state = await state.get_state()  # resets state
        if current_state is not None:
            await state.finish()
    markup = keyboards.main_menu()
    if is_admin(message.from_user.id):
        markup = keyboards.main_menu(admin=True)
    return await message.answer("Welcome!", reply_markup=markup)


@dp.message_handler(commands='cancel', state='*')
@dp.message_handler(Text(equals='Cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('Canceled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands='state', state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    await message.reply(f'{current_state}')


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
    markup = keyboards.main_menu()
    if is_admin(message.from_user.id):
        markup = keyboards.main_menu(admin=True)
    return await message.answer("Welcome!", reply_markup=markup)


@dp.message_handler(state=states.NewUser.phone)
async def process_phone(message: Message, state: FSMContext):
    try:
        user_number = phonenumbers.parse(message.text, None)
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
    markup = keyboards.main_menu()
    if is_admin(message.from_user.id):
        markup = keyboards.main_menu(admin=True)
    return await message.answer("Welcome!", reply_markup=markup)


@dp.callback_query_handler(Text(equals='change_pii', ignore_case=True))
async def process_term(query: types.CallbackQuery):
    await query.answer()
    await query.message.answer("Please enter your name:", reply_markup=ReplyKeyboardRemove())
    await states.NewUser.name.set()

@dp.message_handler(state='*', commands=['admin_rights'])
async def grant_admin_rights(message: Message, state: FSMContext):
    argument = message.get_args()

    if not is_admin_exists():
        await message.answer("No one has admin rights on the database. Enabling admin rights for your account...")
        if switch_admin(message.from_user.id):
            await message.answer("Done!")
            await cmd_start_alt(message, state)
        else:
            await message.answer("Something went wrong.")

    if argument:
        if is_admin(message.from_user.id):
            if (not argument.isdigit()):
                return await message.answer("Unrecognized argument.")
            switch_result = switch_admin(message.from_user.id)
            if switch_result == True:
                await message.answer("Admin rights enabled successfully!")
            elif switch_result == False:
                await message.answer("Admin rights disabled successfully!")
            elif switch_result == None:
                await message.answer("Can't find this user in database.")
