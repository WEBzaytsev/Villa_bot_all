import datetime

from peewee import (AutoField, BigIntegerField, BooleanField, CharField,
                    DateTimeField, FloatField, ForeignKeyField, IntegerField,
                    Model, PostgresqlDatabase, TextField)
from playhouse.postgres_ext import BinaryJSONField

# TODO: use other table/db for apartment parsing
db = PostgresqlDatabase('villabot', user='villauser', password='villapass',
                        host='db', port=5432)


class BaseModel(Model):
    class Meta:
        database = db


class Client(BaseModel):
    tgid = BigIntegerField(unique=True)
    name = CharField(null=True)
    phone = CharField(null=True)
    is_admin = BooleanField(default=False)
    is_rentee = BooleanField(default=False)
    is_renter = BooleanField(default=False)
    notifications = BooleanField(default=True)


class Location(BaseModel):
    name = CharField()
    parent = ForeignKeyField('self', backref='subcategory', null=True)


class Apartment(BaseModel):
    user = ForeignKeyField(Client, backref='apartments', null=True)
    author = CharField(null=True)
    author_id = BigIntegerField(null=True)
    bedrooms = IntegerField(null=True)
    description = TextField(null=True)
    location = ForeignKeyField(Location, backref='apartments')
    phone = CharField(max_length=15, null=True)
    listing_id = BigIntegerField(null=True)
    listdate = DateTimeField(default=datetime.datetime.now)
    delistdate = DateTimeField(null=True)
    checkindate = DateTimeField(null=True)
    shortcode = CharField(null=True)  # TODO: unique
    external = BooleanField(default=False)
    lat = FloatField(null=True)
    lon = FloatField(null=True)
    delisted = BooleanField(default=False)
    deleted = BooleanField(default=False)


class ApartmentMedia(BaseModel):
    apartment = ForeignKeyField(
        Apartment, backref='media', on_delete='CASCADE')
    file_id = CharField()
    # file_type = CharField() # there would be video in media


class ApartmentPrice(BaseModel):
    apartment = ForeignKeyField(
        Apartment, backref='prices', on_delete='CASCADE', unique=True)
    # TODO: probably needs BigIntegerField instead
    day = IntegerField(null=True)
    month = IntegerField(null=True)
    year = IntegerField(null=True)


class ApartmentTerm(BaseModel):
    apartment = ForeignKeyField(
        Apartment, backref='terms', on_delete='CASCADE', unique=True)
    day = BooleanField(default=False)
    month = BooleanField(default=False)
    year = BooleanField(default=False)


class ClientSearch(BaseModel):
    # TODO: FOLLOW UP: Recheck each hour and send differences.
    user = ForeignKeyField(Client, backref='searches')
    last_search_params = None
    last_search_followup_date = DateTimeField(null=True)


class ClientFavorite(BaseModel):
    user = ForeignKeyField(Client, backref='favorites')
    apartment = ForeignKeyField(Apartment)


class Facility(BaseModel):
    facilityid = AutoField()
    name = CharField()


class ApartmentFacility(BaseModel):
    apartment = ForeignKeyField(
        Apartment, backref='facilities', on_delete='CASCADE')
    facility = ForeignKeyField(Facility)


class Appointment(BaseModel):
    apartment = ForeignKeyField(Apartment, backref='appointments')
    client = ForeignKeyField(Client, backref='appointments')
    datestart = DateTimeField(null=True)
    dateend = DateTimeField(null=True)
    canceled = BooleanField(null=True)


class Action(BaseModel):
    name = CharField()


class UserAction(BaseModel):
    client = ForeignKeyField(Client, backref='actions')
    action = ForeignKeyField(Action, backref='actions')
    payload = BinaryJSONField(null=True)
    time = DateTimeField(default=datetime.datetime.now)


class Feedback(BaseModel):
    user = ForeignKeyField(Client, backref='feedback')
    message = TextField()


db.create_tables([Client, Apartment, Appointment, ApartmentMedia, ApartmentFacility,
                 ClientFavorite, ClientSearch, Facility, ApartmentPrice, Location, UserAction, Feedback])
