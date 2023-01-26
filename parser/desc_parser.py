import unicodedata

import extractors


def parse_text_api(test_listing):
    try:
        data = test_listing['data']['viewer']['marketplace_product_details_page']
    except Exception as e:
        try:
            data = test_listing
        except Exception as e:
            return {"author": None, "author_id": None,
                    "bedrooms": None, "description": None, "location": None, "phone": None, "listing_id": None, "price": None, 'photos': [], 'facilities': None, 'terms': None}
    category = None
    bedrooms_int = None
    rentals_category = ['propertyforsale', 'propertyrentals']
    # awful
    try:
        caterogy = data['target']['marketplace_listing_category']['slug']
    except:
        try:
            category = data['marketplace_listing_renderable_target']['seo_virtual_category']['taxonomy_path'][0]['seo_info']['seo_url']
        except:
            pass
    if category in rentals_category or True:
        listing_id = data['target']['id']
        listing_title = data['target'].get('marketplace_listing_title', None)
        listing_price = str(data['target']['listing_price']['amount']
                            ) if data['target']['listing_price']['currency'] == 'IDR' else 0
        listing_seller = data['target']['marketplace_listing_seller']['name']
        listing_seller_id = data['target']['marketplace_listing_seller']['id']

        listing_desc = unicodedata.normalize(
            'NFKC', data['target']['redacted_description']['text'])

        images_list = []
        listing_photos = data['target'].get('listing_photos', None)
        if listing_photos:
            images_list = extractors.extract_images(listing_photos)
        final_price = None

        parsed_location = extractors.extract_location(listing_desc)
        if not parsed_location:
            parsed_location = extractors.extract_location(listing_title)

        pdp_display_sections = data['target'].get('pdp_display_sections', None)
        if pdp_display_sections:
            pdp_info = extractors.extract_pdp_display_sections_info(
                pdp_display_sections)
            bedrooms_int = pdp_info.get('bedrooms', None)
        if not bedrooms_int:
            bedrooms_int = extractors.extract_bedrooms(listing_desc)
        if not bedrooms_int:
            bedrooms_int = extractors.extract_bedrooms(listing_title)

        terms = extractors.extract_term(listing_desc)

        # TODO: implement [hidden information] bypass
        # TODO: iterate each line separately
        cleared_desc = listing_desc.replace("\n", "").replace(
            ",", "").replace("-", "").replace("‐", "").replace(" ", "")
        cleared_desc_keep_newlines = listing_desc.replace(
            ",", "").replace("-", "").replace("‐", "").replace(" ", "")
        cleared_desc_dotless = cleared_desc.replace(".", "")

        number = extractors.extract_number(cleared_desc_dotless)
        facilities = extractors.extract_facilities(listing_desc)
        listing_price_desc = extractors.extract_price(
            cleared_desc_keep_newlines)
        if listing_price_desc:
            for listing_price_ in listing_price_desc:
                if listing_price_.startswith(listing_price) and not listing_price_.startswith(('2022', '2023')):
                    final_price = listing_price_
                    break
        else:
            if not str(listing_price).startswith(('123')):
                final_price = listing_price

        return {"author": listing_seller, "author_id": listing_seller_id,
                "bedrooms": bedrooms_int, "description": listing_desc, "location": parsed_location, "phone": number, "listing_id": listing_id, "price": final_price, 'photos': images_list, 'facilities': facilities, 'terms': terms}
