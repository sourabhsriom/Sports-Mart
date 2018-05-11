import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class catItem(Base):
    __tablename__ = 'catItem'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

class User(Base):
    __tablename__ = 'users'

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key=True)
    password_hash = Column(String(64), nullable=False)

    def hash_password(self, passwd) :
        self.password_hash = pwd_context.encrypt(passwd)

    def verify_password(self, passwd) :
        return pwd_context.verify(passwd, self.password_hash)






engine = create_engine('sqlite:///sportsmart.db')


Base.metadata.create_all(engine)
