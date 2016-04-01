# -*- coding: utf-8 -*-

import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, asc

Base = declarative_base()


class Image(Base):
    __tablename__ = 'image'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=True)
    link = Column(String(250), nullable=False)
    description = Column(Text, nullable=True)


class Tags(Base):
    __tablename__ = 'tags'

    tag = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('image.id'))
    image = relationship(Image)

#class TagLookup(Base):
#    __tablename__ = 'tag_lookup'
#
#    tag_id = Column(Interger, ForeignKey('tag.id'), nullable=False)
#    image_id = Column(Interger, ForiegnKey('image.id'), nullable=False)



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


#engine = create_engine('sqlite:///application.db')
engine = create_engine('postgresql:///catalog')


Base.metadata.create_all(engine)
