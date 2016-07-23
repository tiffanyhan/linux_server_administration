from flask import Flask, render_template, flash, url_for, redirect, request, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

def getSession():
	engine = create_engine('sqlite:///restaurantmenu.db')
	Base.metadata.bind = engine
	DBSession = sessionmaker(bind=engine)
	session = DBSession()
	return session

@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
	session = getSession()
	restaurants = session.query(Restaurant).all()

	if restaurants == []:
		flash('You currently have no restaurants to list')

	session.close()
	return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurant/new/', methods = ['GET', 'POST'])
def newRestaurant():
	if request.method == 'POST':
		newName = request.form['name']

		if not newName:
			error = 'Please enter in a new restaurant name'
			return render_template('newRestaurant.html', error=error)

		else:
			session = getSession()
			newRestaurant = Restaurant(name = newName)
			session.add(newRestaurant)
			session.commit()
			flash("New restaurant created!")

			session.close()
			return redirect(url_for('showRestaurants'))

	else:
		return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
	session = getSession()
	restaurantToEdit = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

	if request.method == 'POST':
		editedName = request.form['name']

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
			flash("Restaurant name edited")

			session.close()
			return redirect(url_for('showRestaurants'))


	else:
		session.close()
		return render_template('editRestaurant.html',
								restaurant_id = restaurant_id,
								restaurant = restaurantToEdit)

@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	session = getSession()
	restaurantToDelete = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

	if request.method == 'POST':
		session.delete(restaurantToDelete)
		session.commit()
		flash("Restaurant deleted")

		session.close()
		return redirect(url_for('showRestaurants'))

	else:
		session.close()
		return render_template('deleteRestaurant.html',
								restaurant_id = restaurant_id,
								restaurant = restaurantToDelete)

@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()

	appetizers = []
	entrees = []
	desserts = []
	beverages = []

	if items == []:
		flash('You currently have no items in this menu')

	else:
		for item in items:
			if item.course == 'Appetizer':
				appetizers.append(item)
			elif item.course == 'Entree':
				entrees.append(item)
			elif item.course == 'Dessert':
				desserts.append(item)
			elif item.course == 'Beverage':
				beverages.append(item)

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

	if request.method == 'POST':
		name = request.form['name'].encode('latin-1')
		price = request.form['price'].encode('latin-1')
		description = request.form['description'].encode('latin-1')
		course = request.form['course'].encode('latin-1')


		if name and price and description and course:
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

	else:
		restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

		session.close()
		return render_template('newMenuItem.html',
								restaurant_id = restaurant_id,
								restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	session = getSession()
	itemToBeEdited = session.query(MenuItem).filter_by(menu_id = menu_id).one()

	if request.method == 'POST':
		if request.form['name']:
			itemToBeEdited.name = request.form['name']
		if request.form['course']:
			itemToBeEdited.course = request.form['course']
		if request.form['description']:
			itemToBeEdited.description = request.form['description']
		if request.form['price']:
			itemToBeEdited.price = request.form['price']

		session.add(itemToBeEdited)
		session.commit()
		flash("Menu item edited")

		session.close()
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))

	else:
		restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

		session.close()
		return render_template('editMenuItem.html',
								restaurant_id = restaurant_id,
								menu_id = menu_id,
								restaurant = restaurant,
								item = itemToBeEdited)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	session = getSession()
	itemToBeDeleted = session.query(MenuItem).filter_by(menu_id = menu_id).one()

	if request.method == 'POST':
		session.delete(itemToBeDeleted)
		session.commit()
		flash("Menu item deleted")

		session.close()
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))

	else:
		restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

		session.close()
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