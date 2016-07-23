restaurants = document.getElementsByClassName('restaurant-item')

restaurants.addEventListener('mouseover', function(event) {
	event.target.style.color = 'grey';
});