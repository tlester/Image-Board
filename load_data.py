# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Image, Tags

# Connect to Database and create database session
engine = create_engine('sqlite:///application.db')
#engine = create_engine('postgresql://vagrant@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add a few images
image = Image(name='Thong',
              link='https://vanitymiami.com/Content/themes/avada/img/procedures/bbl/miami-thong-lift.jpg',
              description='A beautiful butt in a thong')

session.add(image)
session.commit()

tags = ['sunset', 'outdoors', 'beach', 'nature']

for tag in tags:
    tag = Tags(tag=tag, image_id=1)
    session.add(tag)


image = Image(name='Beautiful woman',
               link='http://dreamatico.com/data_images/girl/girl-8.jpg',
               description='A beautiful woman')

session.add(image)

tags = ['woman', 'girl', 'beautiful', 'face']

for tag in tags:
    tag = Tags(tag=tag, image_id=1)
    session.add(tag)

session.commit()
