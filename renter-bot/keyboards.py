from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from aiogram.utils.callback_data import CallbackData

choicer_cb = CallbackData('toggle', 'state', 'button')
pager_cb = CallbackData('page', 'state', 'button')
price_cb = CallbackData('price', 'action', 'term')
villalist_cb = CallbackData('villa', 'id', 'action')
edit_cb = CallbackData('choose', 'attrib', 'value')

main_menu = InlineKeyboardMarkup(row_width=1) \
    .add(InlineKeyboardButton('📥 Add villa', callback_data='add_villa')) \
    .add(InlineKeyboardButton('👤 Fill out contact information', callback_data='change_pii'))\
    .add(InlineKeyboardButton('✏ Change villa info', callback_data='change_villa'))\
    # TODO: .add(InlineKeyboardButton('🙋 Feedback', callback_data='feedback'))\

search_menu = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True) \
    .add(KeyboardButton("Main menu"))

remove_kb = ReplyKeyboardRemove()

admin_main_menu = main_menu.add(InlineKeyboardButton(
    '🛠️ Admin menu', callback_data='admin_menu'))


def villa_keyboard(apart_id):
    # TODO: change photos -> sends photo with buttons, where you can remove/add new photo
    # TODO: dynamic buttons
    markup = InlineKeyboardMarkup(row_width=2)\
        .add(InlineKeyboardButton('Change prices', callback_data=villalist_cb.new(
            id=apart_id, action='price')))\
        .add(InlineKeyboardButton('Change terms', callback_data=villalist_cb.new(
            id=apart_id, action='term')))\
        .add(InlineKeyboardButton('Change location', callback_data=villalist_cb.new(
            id=apart_id, action='location')))\
        .add(InlineKeyboardButton('Change bedrooms', callback_data=villalist_cb.new(
            id=apart_id, action='bedrooms')))\
        .add(InlineKeyboardButton('Change facilities', callback_data=villalist_cb.new(
            id=apart_id, action='facilities')))\
        .add(InlineKeyboardButton('Change photos', callback_data=villalist_cb.new(
            id=apart_id, action='photos')))\
        .add(InlineKeyboardButton('Toggle visibility', callback_data=villalist_cb.new(
            id=apart_id, action='toggle')))\
        .add(InlineKeyboardButton('Remove listing', callback_data=villalist_cb.new(
            id=apart_id, action='remove')))
    return markup


admin_menu = InlineKeyboardMarkup(row_width=1) \
    .add(InlineKeyboardButton('✏ Edit listing', callback_data='admin_edit')) \
    .add(InlineKeyboardButton('📜 Stats', callback_data='admin_stats')) \
    .add(InlineKeyboardButton('📣 Broadcasting', callback_data='admin_broadcast'))


def broadcast_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)\
        .add(InlineKeyboardButton('Change text', callback_data='change_text'))\
        .add(InlineKeyboardButton('Target prices', callback_data='target_price'))\
        .add(InlineKeyboardButton('Target terms', callback_data='target_terms'))\
        .add(InlineKeyboardButton('Target location', callback_data='target_location'))\
        .add(InlineKeyboardButton('Target bedrooms', callback_data='target_bedrooms'))\
        .add(InlineKeyboardButton('Send', callback_data='send_broadcast'))
    # .add(InlineKeyboardButton('Target facilities', callback_data='target_facilities'))\
    return markup
