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

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Image Board"

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as {}".format(login_session['username']))
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



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


@app.route('/images/<int:image_id>/edit', methods=['GET', 'POST'])
def editImage(image_id):
    """ Page for editing an image
    """

    image = session.query(Image).filter_by(id = image_id).one()
    existing_tags = []
    for tag in image.tags:
        existing_tags.append(tag.tag)
    tags = ', '.join(existing_tags)

    if request.method == 'POST':
        image.name = request.form['image_name']
        image.link = request.form['image_url']
        image.description = request.form['image_description']
        session.add(image)
        session.commit()

        for tag in image.tags:
            session.delete(tag)
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
            image.tags.append(tag)
            session.commit()

        return redirect(url_for('image', image_id=image.id))
    return render_template('edit_image.html', image=image, tags=tags)


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
