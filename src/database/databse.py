import json
from pathlib import Path

import firebase_admin
from firebase_admin import db

cred_obj = firebase_admin.credentials.Certificate("./pure-pulsars-firebase-adminsdk-e6qzr-f209635a5a.json")
default_app = firebase_admin.initialize_app(
    cred_obj,
    {
        "databaseURL": "https://pure-pulsars-default-rtdb.firebaseio.com/",
    },
)


ref = db.reference("/")


with Path("src\\database\\test.json").open("r") as f:
    file_contents = json.load(f)
ref.set(file_contents)
