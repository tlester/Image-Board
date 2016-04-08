# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Image, Tags, Users
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Connect to Database and create database session
engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Image Board"

@app.route('/login')
def showLogin():
    """ Login route and controller.  Sets state token to prevent
        forgery.

        Args:
            None

        Returns:
            login.html Template.  The following variable are passed to the
            template:
                - state:  The state key
                - login_session:  Login session object
                - referrer:  The page the user is coming from
    """

    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state,
                           login_session=login_session,
                           referrer=request.referrer)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ Authenticate via Google's OAuth2 service.

        Args:
            None

        Returns:
            auth_results.html template.  The following object is passed to
            the template:
                - login_session: Login session object
            response (if unsuccessful):  http response

    """

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
    print "LOGIN VERIFY URL: {}".format(url)
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

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is '
                                            'already connected.'),
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
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Add flash message to confirm user is logged in.
    flash('you are now logged in as {}'.format(login_session['username']),
          'success')
    print "done!"
    return render_template('auth_results.html', login_session=login_session)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """ Authenticate via Facebook's OAuth2 service

        Args:
            None

        Returns:
            auth_results.html template.  The following object is passed to
            the template:
                - login_session:  Login session object
            response (if unsuccessful): http response
    """

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received {} ".format(access_token)

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={}&client_secret={}&fb_exchange_token={}'.format(app_id, app_secret, access_token)  # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?{}&fields=name,id,email'.format(token)  # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly
    # logout, let's strip out the information before the equals sign
    # in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?{}&redirect=0&height=200&width=200'.format(token)  # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash('Now logged in as {}'.format(login_session['username']), 'success')
    return render_template('auth_results.html', login_session=login_session)

@app.route('/fbdisconnect')
def fbdisconnect():
    """ Asks Facebook to delete user's token.

        Args:
            None

        Returns:
            result:  result of the http delete
    """

    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/{}/permissions?access_token={}'.format(facebook_id, access_token)  # NOQA
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return result


@app.route('/images')
@app.route('/')
def home():
    """ Main landing page for catalog app.  Pulls all the images and
        displays them on the page.

        Args:
            None

        Returns:
            home.html template.  The following are passed into the
            template as variables:
                - images: the images object
                - login_session:  Login session object
    """

    images = session.query(Image).all()
    return render_template('home.html', images=images,
                           login_session=login_session)


@app.route('/images/JSON')
def imagesJSON():
    """ JSON output for all the images

        Args:
            None

        Returns:
            JSON output for all images
    """

    images = session.query(Image).all()
    return jsonify(Images=[i.serialize for i in images])


@app.route('/tags/')
def tags():
    """ A page displaying each tag

        Args:
            None

        Returns:
            tags.html template.  The following are passed into the
            template as variables:
                - tags:  tags object
                - login_session:  Login session object
    """

    tags = session.query(Tags).all()
    return render_template('tags.html', tags=tags, login_session=login_session)


@app.route('/tags/JSON')
def tagsJSON():
    """ A page displaying each tag

        Args:
            None

        Returns:
            JSON output for all tags
    """

    tags = session.query(Tags).all()
    return jsonify(Tags=[t.serialize for t in tags])


@app.route('/tag/<int:tag_id>/')
def tag(tag_id):
    """ Tag page, showing all images for a tag

        Args:
            tag_id:  Integer, primary key of the tag

        Returns:
            tag.html.  The folloiwng are passed into the template
            as variables:
                - tag:  tag object
                - images:  images object
                - login_session:  Login session object
    """

    tag = session.query(Tags).filter_by(id=tag_id).one()
    images = tag.images
    return render_template('tag.html', tag=tag,
                           images=images, login_session=login_session)


@app.route('/tag/<int:tag_id>/JSON')
def tagJSON(tag_id):
    """ Tag page, showing all images for a tag

        Args:
            tag_id:  Integer, primary key of the tag

        Returns:
            JSON output for the tag
    """

    tag = session.query(Tags).filter_by(id=tag_id).one()
    return jsonify(Tags=[tag.serialize])


@app.route('/image/<int:image_id>/')
def image(image_id):
    """ Main page for an individual image

        Args:
            image_id:  Integer, primary key of the image

        Returns:
            image.html.  The folloiwng are passed into the template
            as variables:
                - image:  The image object
                - tags:  The tags object
                - login_session:  The login session object
    """

    image = session.query(Image).filter_by(id=image_id).one()
    tags = image.tags
    return render_template('image.html', image=image,
                           tags=tags, login_session=login_session)


@app.route('/image/<int:image_id>/JSON')
def imageJSON(image_id):
    """ Main page for an individual image

        Args:
            image_id:  Integer, primary key of the image

        Returns:
            JSON output for the image
    """

    image = session.query(Image).filter_by(id=image_id).one()
    return jsonify(Image=[image.serialize])


@app.route('/image/<int:image_id>/edit', methods=['GET', 'POST'])
def editImage(image_id):
    """ Page for editing an image

        Args:
            image_id:  Integer, primary key of the image

        Returns:
            image.html.  The folloiwng are passed into the template
            as variables:
                - image:  The image object
                - tags:  The tags object
                - login_session:  The login session object
    """

    image = session.query(Image).filter_by(id=image_id).one()
    existing_tags = []
    for tag in image.tags:
        existing_tags.append(tag.tag)
    tags = ', '.join(existing_tags)

    # If post, make the required changes
    if request.method == 'POST':
        image.name = request.form['image_name']
        image.link = request.form['image_url']
        image.description = request.form['image_description']
        session.add(image)
        session.commit()

        # Loop through each of the tags
        for tag in image.tags:
            session.delete(tag)
        session.commit()

        tags = request.form['tags'].split(',')
        for tag in tags:
            tag = tag.strip().lower()
            try:
                tag = session.query(Tags).filter_by(tag=tag).one()
            except:
                print 'Adding tag {}'.format(tag)
                tag = Tags(tag=tag)
                session.add(tag)
                session.commit()
            image.tags.append(tag)
            session.commit()

        flash('{} has been successfully updated'.format(image.name), 'success')
        return redirect(url_for('image', image_id=image.id))
    return render_template('edit_image.html',
                           image=image, tags=tags,
                           login_session=login_session)


@app.route('/image/<int:image_id>/delete', methods=['GET', 'POST'])
def deleteImage(image_id):
    """ Prompt to delete an image

        Args:
            image_id:  Integer, primary key of the image

        Returns:
            image.html.  The folloiwng are passed into the template
            as variables:
                - image:  The image object
                - tags:  The tags object
                - login_session:  The login session object
    """

    image = session.query(Image).filter_by(id=image_id).one()
    image_name = image.name
    if request.method == 'POST':
        session.delete(image)
        session.commit()
        flash('{} has been successfully '
              'deleted.'.format(image_name), 'success')
        return redirect(url_for('home'))

    return render_template('delete_image.html',
                           image=image, login_session=login_session)


@app.route('/images/new', methods=['GET', 'POST'])
def newImage():
    """ Create new image

        Args:
            None

        Returns:
            new_image.html template.  The following are passed to the
            template as variables:
                - login_session:  The login session object
    """

    if request.method == 'POST':
        new_image = Image(name=request.form['image_name'],
                          link=request.form['image_url'],
                          description=request.form['image_description'],
                          user_id=login_session['user_id'])
        session.add(new_image)
        session.commit()

        tags = request.form['tags'].split(',')
        # loop through each tag and add
        for tag in tags:
            tag = tag.strip().lower()
            try:
                tag = session.query(Tags).filter_by(tag=tag).one()
            except:
                print 'Adding tag {}'.format(tag)
                tag = Tags(tag=tag)
                session.add(tag)
                session.commit()
            new_image.tags.append(tag)
            session.commit()

        flash('{} has been created '
              'successfully!'.format(request.form['image_name']), 'success')

        return redirect(url_for('home'))
    return render_template('new_image.html', login_session=login_session)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    """ Universal disconnect.  Determine the provider the user
        used to login with, then call that providers's disconnect
        function.

        Args:
            None

        Returns:
            redirects to the home page
    """

    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            results = gdisconnect()
            if results.status_code != 200:
                flash('Log out failed', 'error')
                return redirect(url_for('home'))
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            results = fbdisconnect()
            if 'true' not in results:
                print 'Failed to log out'
                flash('Log out failed', 'error')
                return redirect(url_for('home'))
            del login_session['facebook_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash('You have successfully been logged out.', 'success')
        return redirect(url_for('home'))
    else:
        flash('You were not logged in', 'warning')
        return redirect(url_for('home'))


# User Helper Functions
def createUser(login_session):
    """ If a user logs in for the first time, create their user in the DB

        Args:
            login_sesion:  Login session object
        Returns
            user.id:  Integer:  The primary key of the user
    """

    newUser = Users(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(Users).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """ Get the user info for a user_id

        Args:
            user_id: Integer, the user primary key

        Returns:
            user - The user object
    """

    user = session.query(Users).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """ Queries the DB for the user by e-mail.  If user exists,
        returns user.id.  Else, returns "None".

        Args:
            email:  String - The user's e-mail

        Returns:
            If user exists in DB:
                user.id:  Integer, the primary key of the user.
            Else:
                None
    """

    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    """ Disconnect from google (revoke user token)

        Args:
            None

        Returns:
            response:  The http response
    """

    # Only disconnect a connected user.
    credentials = login_session['access_token']
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(access_token)  # NOQA
    print 'LOGOUT URL:  {}'.format(url)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
