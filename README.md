# Image Board [![Build Status](https://travis-ci.org/tlester/Image-Board.svg?branch=master)](https://travis-ci.org/tlester/Image-Board)

Image Board is a catalog of images that represent items.   Like a traditional
catalog, items can be viewed by categories.  In this case, categories are
called "tags".  User's can add images of items they like and then tag them
to associate them with other items that have similar traits.

## Home Page
The main page can be viewed by clicking the "Image Board" menu item.  This
page will display all the images in the database. Clicking on any single
image will take you to that images page where you'll see:
- Image Name
- Image description
- Tags
- Creater

## Tags
The tag page will show all the tags currently used and a thumbnail from an
image that has that tag.  The quantity of images that match that tag is in
parenthesis.  Click on any tag and it will take you to that tag's page.  On
each tag's page, you'll see a collection of images that belong to that tag.

## Authentication
Authentication is provide via Google or Facebook's OAuth2 service.

## Authorization
Once authenticate, the user can create new images.  An authenticated user
may also edit or delete any image they have created.

## Demo site
[DEMO Site](http://ec2-54-213-215-230.us-west-2.compute.amazonaws.com:5000/)


# Installation

## Database Setup

The application can be used with various SQL type databases.  It has been
tested with PostgreSQL.

- Install postgresql on your host.
- Create a DB user
- Create the DB

```
Example on Linux host:

su postgres -c 'createuser -dRS vagrant'
su vagrant -c 'createdb'
su vagrant -c 'createdb catalog'
```

- Edit the following line in application.py and db_setup.py to reflect the database you just created (ourse is called "catalog")

```
engine = create_engine('postgresql:///catalog')
```

## Installing the application

In the directory that you want to install the application, run the following command:

```
https://github.com/tlester/catalog.git
```

## Configure Facebook OAuth2 client

- Go to the [Facebook developer console](https://developers.facebook.com/) and in the dropdown menu next to your login picture, chose "Add New App".
- Follow the instructions that facebook provides.
- Make note of the "app_id" and "app_secret" for your newly created app.
- Create a file in the same directory as the application called "fb_client_secrets.json".  It should look like this:

```
{
  "web": {
    "app_id": "<your_app_id>",
    "app_secret": "<your_app_secret>"
  }
}
```

## Configure Google Oauth2 client

- Go to the [Google Developer console](https://console.developers.google.com/) and in the dropdown menu next to your login picture, chose "Create a project".
- Follow the instructions that google provides.
- Once your app is created, under credentials click on your app name.
- Click "Download JSON".
- Rename the download file as "client_secrets.json" and place it in the application directory.

## Starting the application

Change into the directory you created during installation ("catalog" by default).  Then start the application.


```
Example:

cd catalog
python application.py
```

## Contact info
Name:  Tom Lester
email: tom@tomlester.com
