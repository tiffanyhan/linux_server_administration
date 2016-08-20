from flask import Flask, render_template, flash, url_for, redirect, request, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']

# returns a database session
def getSession():
	engine = create_engine('sqlite:///restaurantmenuwithusers.db')
	Base.metadata.bind = engine
	DBSession = sessionmaker(bind=engine)
	session = DBSession()
	return session

# check is user is logged in: returns true or false
def checkAuth():
	auth = ''
	if 'username' in login_session:
		auth = True
	else:
		auth = False
	return auth

# check if user created this restaurant: returns true or false
def checkCreator(restaurant):
	creator = ''
	if login_session['user_id'] == restaurant.user_id:
		creator = True
	else:
		creator = False
	return creator

# USER HELPER FUNCTIONS
# returns user's user_id from the db, accepts user's email as argument
def getUserID(email):
	session = getSession()
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.user_id
	except:
		return None

# takes user's user_id from the db, returns the user object
def getUserInfo(user_id):
	session = getSession()
	user = session.query(User).filter_by(user_id = user_id).one()
	return user

# takes flask's built-in session object, creates a new user in db,
# and returns the user's user_id from the db
def createUser(login_session):
	newUser = User(name = login_session['username'],
					email = login_session['email'],
					picture = login_session['picture'])
	session = getSession()
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.user_id

# an extra helper function I added: it makes sure the picture stored in the db
# is up-to-date with what the oauth provider has.  takes in a login session
# and returns the user's user_id from the db.
def updatePicture(login_session):
	session = getSession()
	user = session.query(User).filter_by(email = login_session['email']).one()
	user.picture = login_session['picture']
	session.add(user)
	session.commit()
	return user.user_id

# handler for our login page, makes and passes in a state token
@app.route('/login/')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', state=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
	# validate state token
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
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result.get('user_id') != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID doesn't match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Store the access token in the session for later use.
	login_session['provider'] = 'google'
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id
	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']
	# see if user exists, if not then make a new one
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	#updatePicture(login_session)
	login_session['user_id'] = user_id

	flash("you are now logged in as %s" % login_session['username'])
	output = "done!"
	return output

@app.route('/gdisconnect/')
def gdisconnect():
	# Only disconnect a connected user.
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Execute HTTP GET request to revoke current token
	access_token = credentials
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	response = requests.get(url).json()

	if result['status'] != '200':
		response = make_response(
			json.dumps('Failed to revoke token for given user.'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response

@app.route('/fbconnect', methods = ['POST', 'GET'])
def fbconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	access_token = request.data
	# exchange client token for long-lived server-side token
	app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
	app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	# use token to get user info from API
	userinfo_url = 'https://graph.facebook.com/v2.2/me'
	# strip expire tag from access token
	token = result.split('&')[0]

	url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data['name']
	login_session['email'] = data['email']
	login_session['facebook_id'] = data['id']
	# get user picture
	url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)

	login_session['picture'] = data['data']['url']
	# see if user exists
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	# updatePicture(login_session)
	login_session['user_id'] = user_id

	flash("you are now logged in as %s" % login_session['username'])
	output = "done!"
	return output

@app.route('/fbdisconnect/')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	access_token = login_session.get('access_token')
	url = 'https://graph.facebook.com/%s/premissions?access_token=%s' % (facebook_id, access_token)
	h = httplib2.Http()
	result = h.request(url, "DELETE")[1]
	return "you have been logged out"

@app.route('/disconnect/')
def disconnect():
	# if the user is logged in, check to see whether they
	# logged in with fb or google, and call gdisconnect()
	# or fbdisconnect() accordingly
	if 'provider' in login_session:
		if login_session['provider'] == 'google':
			gdisconnect()
			del login_session['gplus_id']
			del login_session['credentials']
		if login_session['provider'] == 'facebook':
			fbdisconnect()
			del login_session['facebook_id']
		# delete everything else in the login session
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		del login_session['provider']
		flash("You have been successsfully logged out.")

		return redirect(url_for('showRestaurants'))
	else:
		flash("You were not logged in")
		return redirect(url_for('showRestaurants'))

@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
	session = getSession()
	restaurants = session.query(Restaurant).all()
	# show all restaurants, unless there are none.
	if restaurants == []:
		flash('You currently have no restaurants to list')

	session.close()
	return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurant/new/', methods = ['GET', 'POST'])
def newRestaurant():
	if request.method == 'POST':
		newName = request.form['name']
		# create a new restsaurant as long as user entered in a name
		if not newName:
			error = 'Please enter in a new restaurant name'
			return render_template('newRestaurant.html', error=error)
		else:
			session = getSession()
			# create the new restaurant, passing in the user
			# as the creator of the restaurant
			newRestaurant = Restaurant(name = newName,
										user_id = login_session['user_id'])
			session.add(newRestaurant)
			session.commit()
			flash("New restaurant created!")

			session.close()
			return redirect(url_for('showRestaurants'))
	# only show form if the user is logged in, otherwise
	# redirect them to the login page
	else:
		if checkAuth() == False:
			return redirect(url_for('showLogin'))
		else:
			return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
	session = getSession()
	restaurantToEdit = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	# check again if user is creator of restaurant
	if request.method == 'POST' and checkCreator(restaurantToEdit):
		editedName = request.form['name']
		# update the restaurant in the db as long as the user inputted a new name
		if not editedName:
			error = 'Please enter in a new restaurant name'
			return render_template('editRestaurant.html',
									restaurant_id = restaurant_id,
									restaurant = restaurantToEdit,
									error=error)

		else:
			restaurantToEdit.name = editedName
			session.add(restaurantToEdit)
			session.commit()
			flash("Restaurant renamed")

			session.close()
			return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	# only show form is user is logged in AND the user is the creator of the
	# restaurant, otherwise redirect them to the login page or to the
	# read-only view of the restaurant menu page
	else:
		session.close()
		if not checkAuth():
			return redirect(url_for('showLogin'))
		elif not checkCreator(restaurantToEdit):
			flash("You must be the creator of this restaurant menu in order to make changes.")
			return redirect(url_for('showMenu', restaurant_id = restaurant_id))
		else:
			return render_template('editRestaurant.html',
									restaurant_id = restaurant_id,
									restaurant = restaurantToEdit)

@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	session = getSession()
	restaurantToDelete = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	# check again if user is creator of restaurant
	if request.method == 'POST' and checkCreator(restaurantToDelete):
		session.delete(restaurantToDelete)
		session.commit()
		flash("Restaurant deleted")

		session.close()
		return redirect(url_for('showRestaurants'))
	# only show form is user is logged in AND the user is the creator of the
	# restaurant, otherwise redirect them to the login page or to the
	# read-only view of the restaurant menu page
	else:
		session.close()
		if not checkAuth():
			return redirect(url_for('showLogin'))
		elif not checkCreator(restaurantToDelete):
			flash("You must be the creator of this restaurant menu in order to make changes.")
			return redirect(url_for('showMenu', restaurant_id = restaurant_id))
		else:
			return render_template('deleteRestaurant.html',
									restaurant_id = restaurant_id,
									restaurant = restaurantToDelete)

@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
	# get all the menu items belonging to this restaurant
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	# create a list for each type of course, and append
	# each menu item accordingly.  this is preparation for
	# displaying menu items by course type.
	appetizers = []
	entrees = []
	desserts = []
	beverages = []

	for item in items:
		if item.course == 'Appetizer':
			appetizers.append(item)
		elif item.course == 'Entree':
			entrees.append(item)
		elif item.course == 'Dessert':
			desserts.append(item)
		elif item.course == 'Beverage':
			beverages.append(item)
	# is user is logged in AND the creator of the restaurant, show the
	# creator view of the restaurant.  otherwise show the public view.
	if not checkAuth() or not checkCreator(restaurant):
		creator = getUserInfo(restaurant.user_id)
		session.close()
		return render_template('publicmenu.html',
								restaurant_id = restaurant_id,
								restaurant = restaurant,
								appetizers = appetizers,
								entrees = entrees,
								desserts = desserts,
								beverages = beverages,
								creator = creator)
	else:
		# the creator view tells the user if there are no items at all
		# in the menu, or if there are no items in each course type
		if items == []:
			flash('You currently have no items in this menu')

		if appetizers == []:
			flash('You currently have no appetizers in this menu')
		if entrees == []:
			flash('You currently have no entrees in this menu')
		if desserts == []:
			flash('You currently have no desserts in this menu')
		if beverages == []:
			flash('You currently have no beverages in this menu')

		session.close()
		return render_template('menu.html',
								restaurant_id = restaurant_id,
								restaurant = restaurant,
								appetizers = appetizers,
								entrees = entrees,
								desserts = desserts,
								beverages = beverages)


@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	# check again if user is creator of restaurant
	if request.method == 'POST' and checkCreator(restaurant):
		# get all the info inputted to the form
		# and create a new menu item using the info
		name = request.form.get('name')
		price = request.form.get('price')
		description = request.form.get('description')
		course = request.form.get('course')
		# make sure everything in form was filled out
		if not name or not price or not description or not course:
			# returns an error message and re-renders form with values
			# saved for the form fields that the user already filled out
			# TODO: return individual errors like name_error, price_error,
			# etc.  passing in values with **params.
			error = 'All form fields are required in order to create a new menu item'
			return render_template('newMenuItem.html',
									restaurant_id = restaurant_id,
									restaurant = restaurant,
									error = error,
									name = name,
									price = price,
									description = description,
									course=course)
		else:
			newItem = MenuItem(name = name,
								course = course,
								description = description,
								price = price,
								restaurant_id = restaurant_id)
			session.add(newItem)
			session.commit()
			flash("New menu item created!")

			session.close()
			return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	# only show form is user is logged in AND the user is the creator of the
	# restaurant, otherwise redirect them to the login page or to the
	# read-only view of the restaurant menu page
	else:
		session.close()
		if not checkAuth():
			return redirect(url_for('showLogin'))
		elif not checkCreator(restaurant):
			flash("You must be the creator of this restaurant menu in order to make changes.")
			return redirect(url_for('showMenu', restaurant_id = restaurant_id))
		else:
			return render_template('newMenuItem.html',
									restaurant_id = restaurant_id,
									restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	itemToBeEdited = session.query(MenuItem).filter_by(menu_id = menu_id).one()
	# check again if user is creator of restaurant
	if request.method == 'POST' and checkCreator(restaurant):
		# get all the info inputted to the form
		# and edit the menu item using the info
		name = request.form.get('name')
		price = request.form.get('price')
		description = request.form.get('description')
		course = request.form.get('course')
		# TODO: by default, a course is always checked.
		# Need to figure out a workaround if we want to
		# implement error handling.
		if name:
			itemToBeEdited.name = name
		if course:
			itemToBeEdited.course = course
		if description:
			itemToBeEdited.description = description
		if price:
			itemToBeEdited.price = price

		session.add(itemToBeEdited)
		session.commit()
		flash("Menu item edited")

		session.close()
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))

	# only show form is user is logged in AND the user is the creator of the
	# restaurant, otherwise redirect them to the login page or to the
	# read-only view of the restaurant menu page
	else:
		session.close()
		if not checkAuth():
			return redirect(url_for('showLogin'))
		elif not checkCreator(restaurant):
			flash("You must be the creator of this restaurant menu in order to make changes.")
			return redirect(url_for('showMenu', restaurant_id = restaurant_id))
		else:
			return render_template('editMenuItem.html',
									restaurant_id = restaurant_id,
									menu_id = menu_id,
									restaurant = restaurant,
									item = itemToBeEdited)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	itemToBeDeleted = session.query(MenuItem).filter_by(menu_id = menu_id).one()
	# check again if user is creator of restaurant
	if request.method == 'POST' and checkCreator(restaurant):
		session.delete(itemToBeDeleted)
		session.commit()
		flash("Menu item deleted")

		session.close()
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	# only show form is user is logged in AND the user is the creator of the
	# restaurant, otherwise redirect them to the login page or to the
	# read-only view of the restaurant menu page
	else:
		session.close()
		if not checkAuth():
			return redirect(url_for('showLogin'))
		elif not checkCreator(restaurant):
			flash("You must be the creator of this restaurant menu in order to make changes.")
			return redirect(url_for('showMenu', restaurant_id = restaurant_id))
		else:
			return render_template('deleteMenuItem.html',
									restaurant_id = restaurant_id,
									menu_id = menu_id,
									restaurant = restaurant,
									item = itemToBeDeleted)

@app.route('/restaurants/JSON/')
def restaurantJSON():
	session = getSession()
	restaurants = session.query(Restaurant).all()

	session.close()
	return jsonify(Restaurants=[restaurant.serialize for restaurant in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()

	session.close()
	return jsonify(MenuItems=[item.serialize for item in items])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def restaurantMenuItemJSON(restaurant_id, menu_id):
	session = getSession()
	item = session.query(MenuItem).filter_by(menu_id = menu_id).one()

	session.close()
	return jsonify(MenuItem=item.serialize)

if __name__ == '__main__':
	app.secret_key = 'imsosecret'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)