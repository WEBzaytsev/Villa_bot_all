import asyncio

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, MediaGroup, Message)

import keyboards
import states
from misc import dp
from orm_utils import (get_appart_info, get_stats, is_admin)

from .change_villa import format_request


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='admin_edit', ignore_case=True), state=states.Menu.admin_menu)
async def cmd_admin(query: CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("< Back", callback_data="admin_menu"))
    await query.message.edit_text("Send villa shortcode:", reply_markup=markup)
    await states.Menu.admin_edit.set()


@dp.message_handler(lambda c: is_admin(c.from_user.id), state=states.Menu.admin_edit)
async def process_shortcode(message: Message, state: FSMContext):
    if message.text:
        text, markup = format_request(message.text)
        if text:
            await message.delete()
            await state.update_data(apartment_id=message.text)
            await state.update_data(apart=get_appart_info(message.text))
            await state.update_data(admin_edit=True)
            await message.answer(
                text[:4096], reply_markup=markup)

            await states.ChangeVilla.villaview.set()
        else:
            await message.delete()
            error = await message.reply('Not found! Try again.')
            await asyncio.sleep(3)
            await error.delete()


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='admin_menu', ignore_case=True), state="*")
async def admin_menu(query: CallbackQuery, state: FSMContext):

    async with state.proxy() as statedata:
        statedata['initial_message'] = query.message.message_id

    await query.answer()
    await query.message.edit_text("Admin menu:", reply_markup=keyboards.admin_menu)
    await states.Menu.admin_menu.set()


@dp.callback_query_handler(lambda c: is_admin(c.from_user.id), Text(equals='admin_stats', ignore_case=True), state=states.Menu.admin_menu)
async def admin_stats(query: CallbackQuery, state: FSMContext):
    stats = get_stats()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("< Back", callback_data="admin_menu"))
    await query.message.edit_text(f"{stats}", reply_markup=markup)
