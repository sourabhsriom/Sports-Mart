import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
import random, string
from datetime import datetime

Base = declarative_base()

secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))

class User(Base):
    __tablename__ = 'User'

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key=True)
    email = Column(String(80), nullable = False)
    '''password_hash = Column(String(64), nullable=False)

    def hash_password(self, passwd) :
        self.password_hash = pwd_context.encrypt(passwd)

    def verify_password(self, passwd) :
        return pwd_context.verify(passwd, self.password_hash)
        '''

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship(User)

class catItem(Base):
    __tablename__ = 'catItem'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    updated_ts = Column(DateTime, default=datetime.utcnow())
    category_id = Column(Integer, ForeignKey('category.id'))
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship(User)
    category = relationship(Category)








engine = create_engine('sqlite:///sportsmart.db')


Base.metadata.create_all(engine)
