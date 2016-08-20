# starting configuration files for sqlalchemy
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# define classes here
class User(Base):
	__tablename__ = 'user'

	user_id = Column(Integer, primary_key = True)
	name = Column(String(80), nullable = False)
	email = Column(String(80), nullable = False)
	picture = Column(String(250))


class Restaurant(Base):
	__tablename__ = 'restaurant'

	name = Column(String(80),
				  nullable = False)
	restaurant_id = Column(Integer,
						   primary_key = True)
	user_id = Column(Integer, ForeignKey('user.user_id'))
	user = relationship(User)
	# add a method to help return a JSON endpoint
	# of the restaurant object's properties
	@property
	def serialize(self):
		return {
			'name': self.name,
			'restaurant_id': self.restaurant_id
		}

class MenuItem(Base):
	__tablename__ = 'menu_item'

	name = Column(String(80),
				  nullable = False)
	menu_id = Column(Integer,
					 primary_key = True)
	course = Column(String(250))
	description = Column(String(250))
	price = Column(String(8))
	restaurant_id = Column(Integer,
						   ForeignKey('restaurant.restaurant_id'))
	restaurant = relationship(Restaurant)
	user_id = Column(Integer, ForeignKey('user.user_id'))
	user = relationship(User)
	# add a method to help return a JSON endpoint
	# of the menu item object's properties
	@property
	def serialize(self):
		return {
			'name': self.name,
			'description': self.description,
			'id': self.menu_id,
			'price': self.price,
			'course': self.course
		}

# Ending configuration files
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.create_all(engine)