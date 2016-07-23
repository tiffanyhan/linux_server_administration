from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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

#@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id)

	session.close()
	return render_template('menu.html', restaurant=restaurant, items=items)

# Task 1: Create route for newMenuItem function here
@app.route('/restaurant/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		session = getSession()
		newItem = MenuItem(name = request.form['name'], restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		flash("new menu item created!")

		session.close()
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))

	else:
		return render_template('newmenuitem.html', restaurant_id = restaurant_id)

# Task 2: Create route for editMenuItem function here
@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	session = getSession()
	editedItem = session.query(MenuItem).filter_by(menu_id = menu_id).one()

	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']

		session.add(editedItem)
		session.commit()
		flash("menu item edited")

		session.close()
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))

	else:
		session.close()
		return render_template('editmenuitem.html',
								restaurant_id = restaurant_id,
								menu_id = menu_id,
								item = editedItem)

# Task 3: Create a route for deleteMenuItem function here
@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	session = getSession()
	deletedItem = session.query(MenuItem).filter_by(menu_id = menu_id).one()

	if request.method == 'POST':
		session.delete(deletedItem)
		session.commit()
		flash("menu item deleted")

		session.close()
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))

	else:
		session.close()
		return render_template('deletemenuitem.html',
								restaurant_id = restaurant_id,
								menu_id = menu_id,
								item = deletedItem)

@app.route('/restaurants/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
	session = getSession()
	restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()

	session.close()
	return jsonify(MenuItems = [item.serialize for item in items])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def menuItemJSON(restaurant_id, menu_id):
	session = getSession()
	item = session.query(MenuItem).filter_by(menu_id = menu_id).one()

	session.close()
	return jsonify(MenuItem = item.serialize)

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)