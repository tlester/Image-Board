# Image Board [![Build Status](https://travis-ci.org/tlester/catalog.svg?branch=master)](https://travis-ci.org/tlester/catalog)

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
