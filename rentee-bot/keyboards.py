from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from aiogram.utils.callback_data import CallbackData

choicer_cb = CallbackData('toggle', 'state', 'button')
pager_cb = CallbackData('page', 'state', 'button')
price_cb = CallbackData('price', 'action', 'term')
villaaction = CallbackData('apart', 'apartid', 'action')

main_menu = InlineKeyboardMarkup(row_width=1)\
    .add(InlineKeyboardButton('🔍 Search villa', callback_data='find_villa'))\
    .add(InlineKeyboardButton('💾 Show saved villa', callback_data='show_saved_villa'))\
    .add(InlineKeyboardButton('👤 Fill out contact information', callback_data='change_pii'))\
    .add(InlineKeyboardButton('🔔 Toggle notifications', callback_data='toggle_notification'))\
    # TODO: .add(InlineKeyboardButton('🔄 Update the last search', callback_data='refresh_last_update'))\
# TODO: .add(InlineKeyboardButton('🙋 Feedback', callback_data='feedback'))\

search_menu = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)\
    .add(KeyboardButton("Main menu"))

remove_kb = ReplyKeyboardRemove()


def contact_keyboard(apart_id):
    markup = InlineKeyboardMarkup(row_width=2)\
        .add(InlineKeyboardButton('👨‍💼 Contact', callback_data=villaaction.new(apartid=apart_id, action='contact')),
             InlineKeyboardButton('🌟 Save', callback_data=villaaction.new(apartid=apart_id, action='save')))

    return markup
