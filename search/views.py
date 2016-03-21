from django.shortcuts import render


def home(request, template_name='index.html'):
	"""
	Home Page view
	"""
	return render(request, template_name,)


def search(request, template_name='search.html'):
	"""
	View to search for Past Images in the database 
	"""
	return render(request, template_name, {})


def upload_card(request, template_name="upload_card.html"):
	"""
	View to create a new card
	"""
	return render(request, template_name, {})
