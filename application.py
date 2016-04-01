# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Image, Tags, Text
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Connect to Database and create database session
engine = create_engine('sqlite:///application.db')
#engine = create_engine('postgresql://vagrant@localhost/catalog')
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
    #tags = session.query(Tags).filter_by(image_id=image.id).all()
    return render_template('home.html', images=images)

@app.route('/image/<int:image_id>/')
def image(image_id):
    """ Main page for an individual image
    """

    image = session.query(Image).filter_by(id = image_id).one()
    tags = session.query(Tags).filter_by(image_id=image_id).all()
    return render_template('image.html', image=image, tags=tags)

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
        tags = request.form['tags'].split(',')

        session.add(new_image)
        session.commit()
        return redirect(url_for('home'))
    return render_template('new_image.html')


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
