import operator
from functools import reduce

from hashids import Hashids
from peewee import fn
from playhouse.shortcuts import model_to_dict

from models import (Action, Apartment, ApartmentFacility, ApartmentMedia,
                    ApartmentPrice, ApartmentTerm, Appointment, Client,
                    ClientFavorite, Facility, Location, UserAction, db)

hashids = Hashids("villabot_salt_k39p", 5,
                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')


def start_user(tgid):
    client = Client.get_or_none(Client.tgid == tgid)
    if client:
        if not client.name or not client.phone:
            return True
        return False
    client = Client()
    client.tgid = tgid
    client.save()

    return True


def change_pii(tgid, name, phone):
    client = Client.get_or_none(Client.tgid == tgid)
    if client:
        if name:
            client.name = name
        if phone:
            client.phone = phone
        client.save()
        return True
    return False


def get_apartment(rid):
    query = Apartment.get_or_none(Apartment.shortcode == rid)
    return query


def new_apartment(tgid, bedrooms, location, facilitylist, pricelist):
    apartment = Apartment()
    apartment.user = Client.get(Client.tgid == tgid)
    apartment.bedrooms = bedrooms
    apartment.location = Location.get(Location.name == location)
    apartment.save()
    apartment.shortcode = hashids.encode(apartment.id)
    apartment.save()
    for facility1 in facilitylist:
        facility2 = ApartmentFacility()
        facility2.apartment = apartment.id
        fac, _ = Facility.get_or_create(name=facility1)
        facility2.facility = fac
        facility2.save()
    if pricelist:
        term = ApartmentTerm()
        term.apartment = apartment.id
        price = ApartmentPrice()
        price.apartment = apartment.id
        for key, value in pricelist.items():
            if value:
                setattr(term, key.lower(), True)
                setattr(price, key.lower(), value)
        term.save()
        price.save()

    return apartment.id


def set_apartment(shortcode, bedrooms=None, location=None, facilitylist=None, pricelist=None, termlist=None):
    apartment = Apartment.get(Apartment.shortcode == shortcode)
    if bedrooms:
        apartment.bedrooms = bedrooms
    if location:
        apartment.location = Location.get(Location.name == location)
    if facilitylist:
        test = ApartmentFacility.delete().where(
            ApartmentFacility.apartment == apartment).execute()
        for facility1 in facilitylist:
            facility2 = ApartmentFacility()
            facility2.apartment = apartment
            facility2.facility = Facility.get(Facility.name == facility1)
            facility2.save()
    if pricelist:
        price = ApartmentPrice.get(ApartmentPrice.apartment == apartment)
        for key, value in pricelist.items():
            if value:
                setattr(price, key.lower(), value)
        price.save()
    if termlist:
        term = ApartmentTerm.get(ApartmentTerm.apartment == apartment)
        for key, value in termlist.items():
            setattr(term, key.lower(), value)
        term.save()
    apartment.save()
    return apartment.id


def set_apartment_media(apartid, fileid):
    media = ApartmentMedia()
    media.apartment = Apartment.get(Apartment.id == apartid)
    media.file_id = fileid
    media.save()


def get_user_apartments(userid, count=10, page=1):
    if userid:
        query = Apartment.select().join(Client).where(Client.tgid == userid)
        return [model_to_dict(c, backrefs=True, max_depth=3,
                              exclude=[ClientFavorite.apartment, Appointment.apartment, ApartmentPrice.id, ApartmentTerm.id]) for c in query]


def get_apart_prices(apartid, term_str=None):
    if term_str:
        query = ApartmentPrice.select().where(
            ApartmentPrice.apartment == apartid).get()
        data = model_to_dict(
            query, exclude=[ApartmentPrice.id, ApartmentPrice.apartment])
        if data:
            return data[term_str.lower()]
    else:
        query = ApartmentPrice.select().where(
            ApartmentPrice.apartment == apartid).get()
        data = model_to_dict(
            query, exclude=[ApartmentPrice.id, ApartmentPrice.apartment])
        if data:
            return data


def get_appart_media(apartid):
    query = ApartmentMedia.select().where(ApartmentMedia.apartment == apartid)
    data = list(query.dicts())
    if data:
        return data


def get_appart_facilities(apartid):
    query = ApartmentFacility.select(ApartmentFacility, Facility).where(
        ApartmentFacility.apartment == apartid).join(Facility)
    data = list(query.dicts())
    returnarray = []
    if data:
        for facility in data:
            returnarray.append(facility['name'])
        return returnarray


def get_appart_info(shortcode):
    apartment = Apartment.select().where(Apartment.shortcode == shortcode)
    if apartment.exists():
        return model_to_dict(apartment.get(), backrefs=True, max_depth=3,
                             exclude=[ClientFavorite.apartment, Appointment.apartment, ApartmentPrice.id, ApartmentTerm.id])
    return None


def toggle_listing(apart):
    apartment = Apartment.get_or_none(Apartment.shortcode == apart)
    if apartment:
        apartment.delisted = not apartment.delisted
        apartment.save()
        return apartment.delisted
    return False


def get_terms(shortcode):
    query = ApartmentPrice.select().where(
        ApartmentPrice.apartment == Apartment.get(Apartment.shortcode == shortcode))
    data = list(query.dicts())
    if data:
        returnlist = [k.upper() for k, v in data.items() if bool(v)]
        return returnlist
    return None


def remove_apartment(shortcode):
    test = Apartment.delete().where(Apartment.shortcode == shortcode).execute()
    return test


def is_admin(tgid):
    query = Client.get(Client.tgid == tgid).is_admin
    return query


def is_admin_exists():
    query = Client.select().where(Client.is_admin == True).count()
    if query:
        return True
    return False


def switch_admin(tgid):
    client = Client.get_or_none(Client.tgid == tgid)
    if client:
        client.is_admin = not client.is_admin
        client.save()
        return client.is_admin
    return None  


def get_custom_user_searches(facility_list=None, location_list=None, term_list=None, bedrooms_list=None, price_list=None, count=False):
    query = UserAction\
        .select(Client.tgid)\
        .join(Client)\
        .distinct()
    where_expression = []

    if term_list:
        for term in term_list:
            where_expression.append(
                (UserAction.payload['term'].contains(term)))

    if location_list:
        for location in location_list:
            where_expression.append(
                (UserAction.payload['location'].contains(location)))

    if facility_list:
        for facility in facility_list:
            where_expression.append(
                (UserAction.payload['facility'].contains(facility)))

    if bedrooms_list:
        for bedrooms in bedrooms_list:
            where_expression.append(
                (UserAction.payload['bedrooms'].contains(bedrooms)))

    if price_list:
        for price in price_list:
            where_expression.append(
                (UserAction.payload['price'].contains(price)))

    # if price:
    #     query = query.join(ApartmentPrice, on=(
    #         Apartment.id == ApartmentPrice.apartment_id))
    #     pricebetween = {"till 1m": [0, 1_000_000],
    #     "1 - 3 m": [1_000_000, 3_000_000],
    #     "3 - 5 m": [3_000_000, 5_000_000],
    #     "> 5 m": [5_000_000],
    #     "till 20 m": [0, 20_000_000],
    #     "20 - 30 m": [20_000_000, 30_000_000],
    #     "30 - 40 m": [30_000_000, 40_000_000],
    #     ">40 m": [40_000_000],
    #     "till 150 m": [0, 150_000_000],
    #     "150 - 250 m": [150_000_000, 250_000_000],
    #     "250 - 400 m": [250_000_000, 400_000_000],
    #     ">400 m": [400_000_000]}
    #     price_value = pricebetween[price]
    #     if len(price_value) == 2:
    #         priceterm = getattr(ApartmentPrice, term.lower())
    #         where_expression.append((priceterm.between(price_value[0], price_value[1])))
    #         if price_value[0] == 0:
    #             query = query.order_by(priceterm, priceterm.desc())
    #     if len(price_value) == 1:
    #         where_expression.append((priceterm > price_value[0]))
    #         query = query.order_by(priceterm, priceterm.asc())
    # #dont show delisted
    action = Action.get(Action.name == 'SEARCH')
    where_expression.append((UserAction.action == action))
    query = query.where(reduce(operator.and_, where_expression))
    cur = db.cursor()
    user_ids = list(set(id for id, in query.tuples()))
    if count:
        return query.count()
    if user_ids:
        return user_ids


def get_stats():
    stats = {}
    for action in Action.select():
        count = UserAction.select().where(UserAction.action == action).count()
        stats[action.name] = count
    return stats
