# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Image, Tags
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Connect to Database and create database session
#engine = create_engine('sqlite:///application.db')
engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

#@app.route('/images/<int:image_id>/')
@app.route('/')
def home():
    """ Main landing page for catalog app
    """

    images = session.query(Image).all()
    return render_template('home.html', images=images)


@app.route('/tags/')
def tags():
    """ A page displaying each tag
    """

    tags = session.query(Tags).all()
    return render_template('tags.html', tags=tags)


@app.route('/tag/<int:tag_id>/')
def tag(tag_id):
    """ Tag page, showing all images for a tag
    """

    tag = session.query(Tags).filter_by(id = tag_id).one()
    images = tag.images
    return render_template('tag.html', tag = tag, images = images)


@app.route('/image/<int:image_id>/')
def image(image_id):
    """ Main page for an individual image
    """

    image = session.query(Image).filter_by(id = image_id).one()
    tags = image.tags
    return render_template('image.html', image=image, tags=tags)


@app.route('/images/<int:image_id>/edit')
def editImage(image_id):
    """ Page for editing an image
    """

    return 'Edit image# {}'.format(image_id)

@app.route('/image/<int:image_id>/delete', methods=['GET', 'POST'])
def deleteImage(image_id):
    """ Prompt to delete an image
    """

    image = session.query(Image).filter_by(id = image_id).one()
    if request.method == 'POST':
        session.delete(image)
        session.commit()
        return redirect(url_for('home'))

    return render_template('delete_image.html', image=image)


@app.route('/images/new', methods=['GET', 'POST'])
def newImage():
    """ Create new image
    """
    if request.method == 'POST':
        new_image = Image(name = request.form['image_name'],
                          link = request.form['image_url'],
                          description = request.form['image_description'])
        session.add(new_image)
        session.commit()

        tags = request.form['tags'].split(',')
        for tag in tags:
            tag = tag.strip().lower()
            try:
                tag = session.query(Tags).filter_by(tag = tag).one()
            except:
                print 'Adding tag {}'.format(tag)
                tag = Tags(tag = tag)
                session.add(tag)
                session.commit()
            new_image.tags.append(tag)
            session.commit()

        return redirect(url_for('home'))
    return render_template('new_image.html')


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
