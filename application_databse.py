# -*- coding: utf-8 -*-

import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, asc

Base = declarative_base()


class Image(Base):
    __tablename__ = 'image'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    link = Column(String(250), primary_key=True, nullable=False)
    description = Column(String(250), nullable=True)


class Tags(Base):
    __tablename__ = 'tags'

    tag = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('image.id'))
    image = relationship(Image)


# We added this serialize function to be able to send JSON objects in a
# serializable format
    #    @property
#    def serialize(self):
#
#        return {
#            'name': self.name,
#            'description': self.description,
#            'id': self.id,
#            'price': self.price,
#            'course': self.course,
#        }


engine = create_engine('sqlite:///application.db')


Base.metadata.create_all(engine)
