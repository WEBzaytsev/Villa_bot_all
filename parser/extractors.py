import re

from dateparser.search import search_dates


def extract(text, regexes):
    matches = []
    for r in regexes:
        matches += re.findall(r, text, re.IGNORECASE)
    if matches:
        return matches
    return None


def extract_term(text):
    # TRIGGERLIST = {"DAY": ["daily", 'day', 'night', 'nightly'],
    #               "MONTH": ['month', 'monthly'],
    #               "YEAR": ['year', 'yearly']}
    TRIGGERLIST = {"DAY": ["[ ]?/[ ]?daily", '[ ]?/[ ]?day', '[ ]?/[ ]?night', '[ ]?/[ ]?nightly', "daily", 'day', 'night',],
                   "MONTH": ['[ ]?/[ ]?month', '[ ]?/[ ]?monthly', 'month', 'monthly'],
                   "YEAR": ['[ ]?/[ ]?year', '[ ]?/[ ]?yearly', '[ ]?/[ ]?year', '[ ]?/[ ]?yearly', 'year', 'yearly']}

    return_list = []
    for k, v in TRIGGERLIST.items():
        for trigger in v:
            if re.search(r'\b' + trigger.lower() + r'\b', text.lower()):
                if k not in return_list:
                    return_list.append(k)
    return return_list


def extract_price(text):
    REGEX_LIST = ['(?:IDR)(\d+)', '(\d+)(?:IDR)',
                  '(?:Rp)(\d+)', '(\d+)(?:Rp)',]

    ABBR_LIST = {'000000': ['million', 'mil']}
    lower_text = text.lower()
    for k, v in ABBR_LIST.items():
        for trigger in v:
            if trigger.lower() in lower_text:
                lower_text = lower_text.replace(trigger, k)

    price = extract(lower_text, REGEX_LIST)

    return price


def extract_location(text):
    LOCATIONS1 = ["Ubud",
                  "Amed",
                  "Tulamben",
                  "Padangbai",
                  "Lovina",
                  "Singaraja",
                  "Umalas",
                  "Canggu",
                  "Badung",
                  "Berawa",
                  "Kerobokan",
                  "Seminyak",
                  "Legian",
                  "Kuta",
                  "Tuban",
                  "Denpasar",
                  "Sanur",
                  "Benoa",
                  "Nusa Dua",
                  "Jimbaran",
                  "Ungasan",
                  "Uluwatu",
                  "Tanah Lot",
                  "Tabanan",
                  "Bukit",
                  "Medewi",
                  "Pemuteran"]
    for location in LOCATIONS1:
        location_search = re.search(location, text, re.IGNORECASE)
        if location_search:
            return location
    return None


def extract_facilities(text):
    listoffac = {'SHAREDPOOL': ["shared"],
                 'PRIVATEPOOL': ["private"],
                 'BATHTUBE': ["bathtub"],
                 'KITCHEN': ["kitchen"],
                 'CLEANING': ["cleaning", "cleaner"],
                 'WIFI': ["wi-fi", "wifi"],
                 'AC': ["conditioning"], }
    appartfac = []
    for k, v in listoffac.items():
        for trigger in v:
            if trigger.lower() in text.lower():
                if k not in appartfac:
                    appartfac.append(k)
    return appartfac


def extract_pdp_display_sections_info(pdp_display_sections):
    payload = {}
    fields = {}
    for section in pdp_display_sections:
        pdp_fields = section.get('pdp_fields', None)
        if pdp_fields:
            for field in pdp_fields:
                if field.get('icon_name', False) and field.get('display_label', False):
                    fields[field['icon_name']] = field['display_label']
    if 'bedrooms-bathrooms' in fields:
        bedrooms_bathrooms_regex = '(\d+)\s[^\s]+\s·\s(\d+)\s[^\s]'
        try:
            search = re.search(bedrooms_bathrooms_regex,
                               fields['bedrooms-bathrooms'])
            payload['bedrooms'] = search[1]
            payload['bathrooms'] = search[2]
        except Exception as e:
            print(e)
    if 'borders' in fields:
        try:
            area = re.sub('\D', '', fields['borders'])
            payload['area'] = int(area)
        except Exception as e:
            print(e)
    if 'clock' in fields:
        try:
            date = search_dates(f"{fields['clock']}")
            payload['date'] = date
        except Exception as e:
            print(e)
    return payload


def extract_number(text):
    REGEX_LIST = ["\+\d{2,3}[\d -]+", "[\D|+](\d{12,13})[\D]", "\d{12,13}"]
    numbers_list = list()

    numbers = extract(text, REGEX_LIST)
    if numbers:
        for number in numbers:
            number = re.sub('\D', '', number)
            if number.startswith('62'):
                numbers_list.append(number)
            if number.startswith('0'):
                countrynumber = number.replace("0", "62", 1)
                numbers_list.append(countrynumber)
        numbers_set = set(numbers_list)
        if numbers_set:
            return list(numbers_set)[0]
    return None


def extract_bedrooms(text):
    BEDROOM_REGEX = re.compile(
        r'(?:([0-9]+)[ ]?(?:br|bed|bd|kamar)|(?:Bedroom|Bed|Beds)[:]?([0-9]+))', re.IGNORECASE)
    bedrooms_int = None
    bedrooms = BEDROOM_REGEX.findall(text)
    if bedrooms:
        for x in list(bedrooms[0]):
            if x.isdigit():
                bedrooms_int = x
    return bedrooms_int


def extract_images(listing_photos):
    images_list = []
    for elem in listing_photos:
        if elem['image']:
            images_list.append(elem['image']['uri'])
    return images_list
