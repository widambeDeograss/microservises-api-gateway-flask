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
json_file_path = os.path.join(root_dir(), "database/showtimes.json")

# Open and load the JSON file
with open(json_file_path, "r") as f:
    showtimes = json.load(f)


@app.route("/", methods=['GET'])
def hello():
    return nice_json({
        "uri": "/",
        "subresource_uris": {
            "showtimes": "/showtimes",
            "showtime": "/showtimes/<date>"
        }
    })


@app.route("/showtimes", methods=['GET'])
def showtimes_list():
    return nice_json(showtimes)


@app.route("/showtimes/<date>", methods=['GET'])
def showtimes_record(date):
    if date not in showtimes:
        raise NotFound
    print(showtimes[date])
    return nice_json(showtimes[date])

if __name__ == "__main__":
    app.run(port=5002, debug=True)
