import operator
from functools import reduce

from peewee import fn
from playhouse.shortcuts import model_to_dict

from models import (Action, Apartment, ApartmentFacility, ApartmentMedia,
                    ApartmentPrice, ApartmentTerm, Client, ClientFavorite,
                    Facility, Location, UserAction)


def start_user(tgid):
    client = Client.get_or_none(Client.tgid == tgid)
    if client:
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


def toggle_notifications(tgid):
    client = Client.get_or_none(Client.tgid == tgid)
    if client:
        client.notifications = not client.notifications
        client.save()
        return client.notifications
    return False


def add_to_favorite(tgid, shortcode):
    client = Client.get_or_none(Client.tgid == tgid)
    apartment = Apartment.get_or_none(Apartment.shortcode == shortcode)
    favorite, created = ClientFavorite.get_or_create(
        user=client, apartment=apartment)
    if created:
        return True
    else:
        favorite.delete_instance()
        return False
# These functions currently being rewrited.


def get_saved_villa(tgid):
    client = Client.get_or_none(Client.tgid == tgid)
    query = ClientFavorite.select(ClientFavorite, Apartment).where(
        ClientFavorite.user == client).join(Apartment)
    data = list(query.dicts())
    if data:
        return data


def get_apartment(rid):
    query = Apartment.get_or_none(Apartment.shortcode == rid)
    return query


def get_apartments(count=10, page=1):
    query = Apartment.select().order_by(
        Apartment.listdate).paginate(page, count)
    data = list(query.dicts())
    if data:
        return data
    return None


def get_appart(facility_list=None, location_list=None, term=None, bedrooms=None, price=None, shortcode=None):
    # TODO: proper data return
    query = Apartment\
        .select()
    where_expression = []

    if term:
        query = query.join(ApartmentTerm, on=(
            Apartment.id == ApartmentTerm.apartment_id))
        where_expression.append((getattr(ApartmentTerm, term.lower()) == True))

    if location_list:
        location_objects = list()
        for location_element in location_list:
            location_objects.append(Location.get(
                Location.name == location_element))
        where_expression.append((Apartment.location << location_objects))

    if facility_list:
        facilities_objects = list()
        for facility_element in facility_list:
            facilities_objects.append(Facility.get(
                Facility.name == facility_element))
        query = query.join(ApartmentFacility, on=(Apartment.id == ApartmentFacility.apartment_id))\
                     .join(Facility, on=(Facility.facilityid == ApartmentFacility.facility_id))

        where_expression.append(
            (ApartmentFacility.facility << facilities_objects))
        # .group_by(Apartment.id)\
        # .having(fn.count(1) == len(facilities_objects))

    if bedrooms:
        where_expression.append(
            (Apartment.bedrooms << bedrooms))
    if price:
        query = query.join(ApartmentPrice, on=(
            Apartment.id == ApartmentPrice.apartment_id))
        pricebetween = {"till 1m": [0, 1_000_000],
                        "1 - 3 m": [1_000_000, 3_000_000],
                        "3 - 5 m": [3_000_000, 5_000_000],
                        "> 5 m": [5_000_000],
                        "till 20 m": [0, 20_000_000],
                        "20 - 30 m": [20_000_000, 30_000_000],
                        "30 - 40 m": [30_000_000, 40_000_000],
                        ">40 m": [40_000_000],
                        "till 150 m": [0, 150_000_000],
                        "150 - 250 m": [150_000_000, 250_000_000],
                        "250 - 400 m": [250_000_000, 400_000_000],
                        ">400 m": [400_000_000]}
        price_value = pricebetween[price]
        if len(price_value) == 2:
            priceterm = getattr(ApartmentPrice, term.lower())
            where_expression.append(
                (priceterm.between(price_value[0], price_value[1])))
            if price_value[0] == 0:
                query = query.order_by(priceterm, priceterm.desc())
        if len(price_value) == 1:
            where_expression.append((priceterm > price_value[0]))
            query = query.order_by(priceterm, priceterm.asc())
    # dont show delisted
    where_expression.append(
        (Apartment.delisted is not False))
    query = query.where(reduce(operator.and_, where_expression))
    data = [model_to_dict(appart, recurse=True) for appart in query]
    if data:
        return data


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


def set_custom_user_search(tgid, facility_list=None, location_list=None, term_list=None, bedrooms_list=None, price_list=None):
    user = Client.get(tgid=tgid)
    jsonfield = {'term': term_list, 'location': location_list,
                 'facility': facility_list, 'bedrooms': bedrooms_list, 'price': price_list}
    UserAction.create(client=user, action=Action.get(
        Action.name == 'SEARCH'), payload=jsonfield)
