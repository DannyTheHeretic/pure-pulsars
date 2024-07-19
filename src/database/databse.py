import firebase_admin

cred_obj = firebase_admin.credentials.Certificate('./pure-pulsars-firebase-adminsdk-e6qzr-f209635a5a.json')
default_app = firebase_admin.initialize_app(cred_obj, {
	'databaseURL': 'https://pure-pulsars-default-rtdb.firebaseio.com/'
	})


from firebase_admin import db

ref = db.reference("/")


import json
with open("src\\database\\test.json", "r") as f:
	file_contents = json.load(f)
ref.set(file_contents)


