from aiogram import types
from aiogram.dispatcher import FSMContext

from misc import dp

from .general_commands import cmd_start_alt
from orm_utils import start_user

@dp.callback_query_handler(state='*')
async def process_term(query: types.CallbackQuery, state: FSMContext):
    await query.answer("Sorry, something went wrong! Restarting from main menu...")
    await query.message.delete()
    user, _ = start_user(query.from_user.id)
    if user.name and user.phone:
        await cmd_start_alt(query.from_user, state)


@dp.message_handler()
async def cancel_handler(message: types.Message, state: FSMContext):
    #await message.reply("Old message. Sending main menu.")
    await message.delete()
    user, _ = start_user(message.from_user.id)
    if user.name and user.phone:
        await cmd_start_alt(message.from_user, state)
