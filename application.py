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

@app.route('/')
@app.route('/images/<int:image_id>/')
def Home(image_id):
    """ Main landing page for catalog app
    """

    image = session.query(Image).filter_by(id = image_id).one()
    tags = session.query(Tags).filter_by(image_id=image.id).all()
    output = ''
    output = image.name
    output += '<br />'
    output += image.link
    output += '<br />'
    output += image.description
    output += '<br />'
    output += '<ul>'
    for tag in tags:
        output += '<li>{}</li>'.format(tag.tag)
    output+= '</ul>'

    return output


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
