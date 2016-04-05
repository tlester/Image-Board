# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


# Lookup table to facility many to many relationship for tags
tag_lookup = Table('tag_lookup',
                   Base.metadata,
                   Column('tag_id', Integer(), ForeignKey('tags.id')),
                   Column('image_id', Integer(), ForeignKey('image.id')))


class Users(Base):
    """ User table
        id = Int, auto-incrementing primary key
        name = String, user's name
        email = String, uer's e-mail
        picture = String, URL to user's profile picture.
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Tags(Base):
    """ Tags table
        id - Int, auto-incrementing primary key
        tag - String, unique tag name
        tags = relationship for backref from Image class
    """
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(String(80), unique=True)
    tags = relationship('Image',
                        secondary=tag_lookup,
                        backref=backref('tags', lazy='dynamic'))

    # serialize function to be able to send JSON objects in a
    # serializable format
    @property
    def serialize(self):

        return {
            'tag': self.tag,
            'id:': self.id,
            'images': [{'id': image.id,
                        'name': image.name,
                        'link': image.link,
                        'description': image.description,
                        'creator': {'id': image.user.id,
                                    'name': image.user.name,
                                    'email': image.user.email,
                                    'picture': image.user.picture}
                        } for image in self.images]
        }


class Image(Base):
    """ Image table
        id - Int, auto-incrementing primary key
        name - String, image name
        link - String, url to image location
        description - Text, description of image
        images - relation ship for backref from Tags class
        user_id - Int, Foreign key for the user who created the image
        user - relationship to User class.
    """
    __tablename__ = 'image'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=True)
    link = Column(String(250), nullable=False)
    description = Column(Text, nullable=True)
    images = relationship('Tags',
                          secondary=tag_lookup,
                          backref=backref('images'),
                          lazy='dynamic')
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(Users)

    # serialize function to be able to send JSON objects in a
    # serializable format
    @property
    def serialize(self):

        return {
            'name': self.name,
            'link': self.link,
            'description': self.description,
            'id': self.id,
            'creator': {'id': self.user.id,
                        'name': self.user.name,
                        'email': self.user.email,
                        'picture': self.user.picture},
            'tags': [tag.tag for tag in self.tags]
        }


engine = create_engine('postgresql:///catalog')
Base.metadata.create_all(engine)
