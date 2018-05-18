from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dbsetup import Category, Base, catItem, User
from datetime import datetime

engine = create_engine('sqlite:///sportsmart.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


user = User(id = 1, name = "Sourabh", email = "sourabh.iitg@gmail.com")

cat1 = Category(name = "Cricket", user_id = 1)

session.add(cat1)
session.commit()

item1 = catItem(name = "bat", description = "a big paddle you use to hit the cricket ball", category = cat1, user_id = 1)
session.add(item1)
session.commit()

item3 = catItem(name = "ball", description = "you flung this to the bowler", category = cat1, user_id = 1)
session.add(item3)
session.commit()

item4 = catItem(name = "stumps", description = "define the ends of the pitch", category = cat1, user_id = 1)
session.add(item4)
session.commit()


cat2 = Category(name = "Football", user_id = 1)

session.add(cat2)
session.commit()

item2 = catItem(name = "gloves", description = "what the goalie uses", category = cat2, user_id = 1)
session.add(item2)
session.commit()

item5 = catItem(name = "shin guards", description = "protective wear for your shins", category = cat2, user_id = 1)
session.add(item5)
session.commit()

cat3 = Category(name = "Hockey", user_id = 1)

session.add(cat3)
session.commit()

item6 = catItem(name = "puck", description = "short cylinder flung across the rink", category = cat3, user_id = 1)
session.add(item6)
session.commit()


item7 = catItem(name = "stick", description = "Like long rod", category = cat3, user_id = 1)
session.add(item7)
session.commit()

item8 = catItem(name = "knee guard", description = "protect yourself from the wrath of the angry puck", category = cat3, user_id = 1)
session.add(item8)
session.commit()
