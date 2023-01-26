from aiogram import types
from aiogram.dispatcher import FSMContext

from misc import dp

from .general_commands import cmd_start_alt


@dp.callback_query_handler(state='*')
async def process_term(query: types.CallbackQuery, state: FSMContext):
    await query.answer("Sorry, something went wrong! Restarting from main menu...")
    await query.message.delete()
    await cmd_start_alt(query.message, state)


@dp.message_handler()
async def cancel_handler(message: types.Message, state: FSMContext):
    #await message.reply("Old message. Sending main menu.")
    await message.delete()
    await cmd_start_alt(message, state)