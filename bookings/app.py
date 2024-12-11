from flask import Flask
from werkzeug.exceptions import NotFound
import os
import json
from flask import make_response

def root_dir():
    """Returns the root directory for this project."""
    return os.path.dirname(os.path.abspath(__file__))

def nice_json(arg):
    response = make_response(json.dumps(arg, sort_keys=True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response

app = Flask(__name__)

# Construct the path to the JSON file
json_file_path = os.path.join(root_dir(), "database/bookings.json")

# Open and load the JSON file
with open(json_file_path, "r") as f:
    bookings = json.load(f)


@app.route("/", methods=['GET'])
def hello():
    return nice_json({
        "uri": "/",
        "subresource_uris": {
            "bookings": "/bookings",
            "booking": "/bookings/<username>"
        }
    })


@app.route("/bookings", methods=['GET'])
def booking_list():
    return nice_json(bookings)


@app.route("/bookings/<username>", methods=['GET'])
def booking_record(username):
    if username not in bookings:
        raise NotFound

    return nice_json(bookings[username])

if __name__ == "__main__":
    app.run(port=5003, debug=True)

