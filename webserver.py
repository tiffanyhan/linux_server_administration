from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

# to access my database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

def getSession():
	engine = create_engine('sqlite:///restaurantmenu.db')
	Base.metadata.bind = engine
	DBSession = sessionmaker(bind = engine)
	session = DBSession()

	return session

class webserverHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			if self.path.endswith("/hello"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body>"
				output += "Hello!"
				output += """<form method='POST' enctype='multipart/form-data' action='/hello'>
							<h2>What would you like me to say?</h2>
							<input name='message' type='text'>
							<input type='submit' value='Submit'>
						</form>"""
				output += "</body></html>"

				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/hola"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body>"
				output += "Hola!"
				output += """<form method='POST' enctype='multipart/form-data' action='/hola'>
							<h2>What would you like me to say?</h2>
							<input name='message' type='text'>
							<input type='submit' value='Submit'>
						</form>"""
				output += "</body></html>"

				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/restaurants"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				session = getSession()
				allRestaurants = session.query(Restaurant).all()

				output = ""
				output += "<html><body>"
				output += "<p><a href='/restaurants/new'>Make a new restaurant here</a></p>"

				for restaurant in allRestaurants:
					output += "<p>"
					output += restaurant.name
					output += "<br>"
					output += "<a href='/restaurants/%s/edit'>Edit</a>" % restaurant.restaurant_id
					output += "<br>"
					output += "<a href='/restaurants/%s/delete'>Delete</a>" % restaurant.restaurant_id
					output += "</p>"
				output += "</body></html>"

				self.wfile.write(output)
				session.close()
				return

			if self.path.endswith("/restaurants/new"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body>"
				output += """<form method='POST' enctype='multipart/form-data' action='/restaurants/new'>
							<h1>Make a new restaurant</h1>
							<input name='restaurant' type='text' placeholder='New Restaurant Name'>
							<input type='submit' value='Create'>
						</form>"""
				output += "</body></html>"

				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/edit"):
				restaurant_id = self.path.split('/')[2]
				session = getSession()
				restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

				if restaurant != []:
					self.send_response(200)
					self.send_header('Content-type', 'text/html')
					self.end_headers()

					output = ""
					output += "<html><body>"
					output += """<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/edit'>
								<h2>%s</h2>
								<input name='editedRestaurantName' type='text' placeholder='Enter a new name'>
								<input type='submit' value='Rename'>
							</form>""" % (restaurant_id, restaurant.name)
					output += "</body></html>"

					self.wfile.write(output)
					session.close()
					return

			if self.path.endswith('/delete'):
				restaurant_id = self.path.split('/')[2]
				session = getSession()
				restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

				if restaurant != []:
					self.send_response(200)
					self.send_header('Content-type', 'text/html')
					self.end_headers()

					output = ""
					output += "<html><body>"
					output += """<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/delete'>
								<h1>Are you sure you want to delete %s?</h1>
								<input type='submit' value='Delete'>
							</form>""" % (restaurant_id, restaurant.name)
					output += "</body></html>"

					self.wfile.write(output)
					session.close()
					return

		except IOError:
			self.send_error(404, "File Not Found %s" % self.path)

	def RedirectTo(self, url, timeout=0):
		self.wfile.write("""<html><head>
							<meta HTTP-EQUIV="REFRESH" content="%i; url=%s"/>
						</head>""" % (timeout, url))

	def do_POST(self):
		try:
			if self.path.endswith("/hello") or self.path.endswith("/hola"):
				self.send_response(301)
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					messagecontent = fields.get('message')

				output = ""
				output += "<html><body"
				output += "<h2>Okay, how about this: </h2>"
				output += "<h1>%s</h1>" % messagecontent[0]

				output += """<form method='POST' enctype='multipart/form-data' action='/hello'>
							<h2>What would you like me to say?</h2>
							<input name='message' type='text'>
							<input type='submit' value='Submit'>
						</form>"""
				output += "</body></html>"

				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/restaurants/new"):
				self.send_response(301)
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					restaurantName = fields.get('restaurant')[0]

				session = getSession()
				newRestaurant = Restaurant(name = restaurantName)
				session.add(newRestaurant)
				session.commit()

				self.RedirectTo('/restaurants')
				session.close()
				return

			if self.path.endswith("/edit"):
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					editedRestaurantName = fields.get('editedRestaurantName')[0]
				restaurant_id = self.path.split('/')[2]

				session = getSession()
				restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

				if restaurant != []:
					restaurant.name = editedRestaurantName
					session.add(restaurant)
					session.commit()

					self.RedirectTo('/restaurants')

				session.close()
				return

			if self.path.endswith("/delete"):
				restaurant_id = self.path.split('/')[2]

				session = getSession()
				restaurant = session.query(Restaurant).filter_by(restaurant_id = restaurant_id).one()

				if restaurant != []:
					session.delete(restaurant)
					session.commit()

					self.RedirectTo('/restaurants')

				session.close()
 				return


		except:
			pass


def main():
	try:
		port = 8080
		server = HTTPServer(('', port), webserverHandler)
		print "Web server running on port %s" % port
		server.serve_forever()

	except KeyboardInterrupt:
		print "Control c entered, stopping web server..."
		server.socket.close()


if __name__ == '__main__':
	main()