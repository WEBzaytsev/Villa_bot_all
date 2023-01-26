import time

from desc_parser import parse_text_api
from fb import get_product_detail_page, search_continious
from orm_utils import get_apartment, new_apartment, set_apartment_media
from settings import SLEEP_INTERVAL
from utils import upload_file_as_renter_bot

prev_list = []
while True:
    print("Getting available listings...")
    market_list = search_continious('villa rent 62', iterations=5)
    if prev_list != market_list:
        diff = [x for x in market_list if x not in prev_list]
        prev_list = prev_list + market_list
        for listing in diff:
            appart = get_apartment(listing)
            if not appart:
                print(f"Getting listing ID {listing}...")
                pdp = get_product_detail_page(listing)
                parse_result = parse_text_api(pdp)
                pricelist = {}
                if parse_result['terms']:
                    for term in parse_result['terms']:
                        pricelist[term] = parse_result['price'] if parse_result['price'] else 0
                else:
                    pricelist['MONTH'] = parse_result['price'] if parse_result['price'] else 0
                if parse_result['terms'] and parse_result['phone'] and parse_result['price'] and parse_result['location']:
                    apart = new_apartment(
                        author=parse_result['author'],
                        author_id=parse_result['author_id'],
                        bedrooms=parse_result['bedrooms'],
                        description=parse_result['description'],
                        phone=parse_result['phone'],
                        listing_id=parse_result['listing_id'],
                        locationlisting=parse_result['location'],
                        facilitylist=parse_result['facilities'],
                        pricelist=pricelist
                    )
                    text = f"""
author={parse_result['author']},
author_id={parse_result['author_id']},
bedrooms={parse_result['bedrooms']},
phone={parse_result['phone']},
listing_id={parse_result['listing_id']},
locationlisting={parse_result['location']},
facilitylist={parse_result['facilities']},
pricelist={pricelist}
                        """
                    if parse_result['photos']:
                        tg_photos = upload_file_as_renter_bot(
                            parse_result['photos'], text)
                        for photo in tg_photos:
                            set_apartment_media(apart, photo)
                        time.sleep(60)
    print("Nothing to parse. Sleeping.")
    time.sleep(SLEEP_INTERVAL)
    continue
