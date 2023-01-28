import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware

from orm_utils import start_user
from states import NewUser


class UserCheckMiddleware(BaseMiddleware):
    def __init__(self,):
        super(UserCheckMiddleware, self).__init__()

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        dispatcher = Dispatcher.get_current()
        state = dispatcher.current_state()
        statename = await state.get_state()
        print(callback_query)
        if callback_query.from_user.id == callback_query.message.chat.id:
            user, created = start_user(callback_query.from_user.id)
            if created:
                await callback_query.message.delete()
                await state.set_state(NewUser.name)
                return await callback_query.message.answer(f"Hello, {callback_query.from_user.first_name}! Please send your name:")
            if not created and user.name is None and statename != "NewUser:name":
                await callback_query.message.delete()
                await state.set_state(NewUser.name)
                return await callback_query.message.answer(f"🧑‍💻 Please send your name:")
            if not created and user.phone is None and statename != "NewUser:phone":
                await callback_query.message.delete()
                await state.set_state(NewUser.phone)
                sharecontact = types.KeyboardButton(
                    'Send contact', request_contact=True)
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)\
                    .add(sharecontact)
                return await callback_query.message.answer("☎️ Please provide your telephone number in international format (e.g.. +628...):", reply_markup=markup)

    async def on_post_process_message(self, message: types.Message, results, data: dict):
        print(results)
        dispatcher = Dispatcher.get_current()
        state = dispatcher.current_state()
        statename = await state.get_state()
        user, created = start_user(message.from_user.id)
        if created:
            await state.set_state(NewUser.name)
            return await message.answer(f"Hello, {message.from_user.first_name}! Please send your name:")
        if not created and user.name is None and statename != "NewUser:name":
            await state.set_state(NewUser.name)
            return await message.answer(f"🧑‍💻 Please send your name:")
        if not created and user.phone is None and statename != "NewUser:phone":
            await state.set_state(NewUser.phone)
            sharecontact = types.KeyboardButton(
                'Send contact', request_contact=True)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)\
                .add(sharecontact)
            return await message.answer("☎️ Please provide your telephone number in international format (e.g.. +628...):", reply_markup=markup)
