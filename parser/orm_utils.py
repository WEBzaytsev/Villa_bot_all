from hashids import Hashids

from models import (Apartment, ApartmentFacility, ApartmentMedia,
                    ApartmentPrice, ApartmentTerm, Facility, Location)

hashids = Hashids("villabot_salt_k39p", 5,
                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')


def get_apartment(listing_id):
    query = Apartment.get_or_none(Apartment.listing_id == listing_id)
    return query


def new_apartment(author, author_id, bedrooms, description, phone, listing_id, locationlisting, facilitylist, pricelist):
    apartment = Apartment()
    apartment.author = author
    apartment.author_id = author_id
    apartment.listing_id = listing_id
    apartment.bedrooms = bedrooms
    apartment.description = description
    apartment.phone = phone
    apartment.external = True
    obj_location, _ = Location.get_or_create(name=locationlisting.upper())
    apartment.location = obj_location
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


def set_apartment_media(apartid, fileid):
    media = ApartmentMedia()
    media.apartment = Apartment.get(Apartment.id == apartid)
    media.file_id = fileid
    media.save()
