from io import BytesIO
from random import choice

import requests
import telebot
from telebot.types import InputMediaPhoto

from constants import googlebot
from proxy import Rotator, proxies
from settings import OWNER_TOKEN, STORAGE_IDS

rotator = Rotator(proxies)


def get_image_by_id(id):
    proxy = rotator.get()
    proxy_list = {'http': str(proxy), 'https': str(proxy)}
    url = f'https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id={id}'
    image_obj = requests.get(url, headers=googlebot,
                             proxies=proxy_list).content
    return image_obj


def get_image_by_url(url):
    # TODO: fallback to lookaside if request failed
    proxy = rotator.get()
    proxy_list = {'http': str(proxy), 'https': str(proxy)}
    image_obj = requests.get(url, headers=googlebot,
                             proxies=proxy_list).content
    return image_obj


def upload_file_as_renter_bot(urls, caption=None):
    if urls:
        bot = telebot.TeleBot(OWNER_TOKEN)
        channel_id = choice(STORAGE_IDS)
        if len(urls) == 1:
            img = BytesIO(get_image_by_url(urls[0]))
            msg = bot.send_photo(channel_id, img)
            return [msg.photo[-1].file_id]
        else:
            if len(urls) > 3:
                urls = urls[:3]
            media_group = []
            return_list = []
            for url in urls:
                img = BytesIO(get_image_by_url(url))
                if len(media_group) == 0 and caption:
                    media_group.append(InputMediaPhoto(img, caption=caption))
                else:
                    media_group.append(InputMediaPhoto(img))
            messages = bot.send_media_group(channel_id, media_group)
            for message in messages:
                return_list.append(message.photo[-1].file_id)
            return return_list
