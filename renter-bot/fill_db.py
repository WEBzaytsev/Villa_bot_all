from models import Action, Facility, Location

# Actions
listoffact = ["START",
              "SEARCH"]

for element in listoffact:
    Action.get_or_create(name=element)

# Facilities
listoffac = ['PRIVATEPOOL',
             'SHAREDPOOL',
             'BATHTUBE',
             'KITCHEN',
             'CLEANING',
             'WIFI',
             'AC',
             'LAUNDRY',
             'DISHWASHER',
             'PETFRIENDLY',]

for element in listoffac:
    Facility.get_or_create(name=element)

# Locations
# TODO: most popular rating
listoffloc = {"Centre": ["Ubud"],
              "East": ["Amed", "Tulamben", "Padangbai"],
              "North": ["Lovina", "Singaraja", "Umalas", "Canggu", "Badung", "Berawa", "Kerobokan", "Seminyak", "Legian", "Kuta", "Tuban", "Denpasar", "Sanur", "Benoa", "Nusa Dua", "Jimbaran", "Ungasan", "Uluwatu", "Tanah Lot", "Tabanan", "Bukit"],
              "West": ["Medewi", "Pemuteran"]
              }


# Terms
listoffterm = ["DAY",
               "MONTH",
               "YEAR",]

# for element in listoffterm:
#    Term.get_or_create(name=element)


for key, val in listoffloc.items():
    # side = Location.get_or_create(name=key) TODO: sides for keyboard
    for i in val:
        # village = Location.get_or_create(name=key, parent=side)
        village = Location.get_or_create(name=i.upper())
        print("{} : {}".format(key, i))
    print("--------------------")
