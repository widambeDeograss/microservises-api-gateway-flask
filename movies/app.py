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
json_file_path = os.path.join(root_dir(), "database/movies.json")

# Open and load the JSON file
with open(json_file_path, "r") as f:
    movies = json.load(f)


@app.route("/", methods=['GET'])
def hello():
    return nice_json({
        "uri": "/",
        "subresource_uris": {
            "movies": "/movies",
            "movie": "/movies/<id>"
        }
    })

@app.route("/movies/<movieid>", methods=['GET'])
def movie_info(movieid):
    if movieid not in movies:
        raise NotFound

    result = movies[movieid]
    result["uri"] = "/movies/{}".format(movieid)

    return nice_json(result)


@app.route("/movies", methods=['GET'])
def movie_record():
    return nice_json(movies)


if __name__ == "__main__":
    app.run(port=5001, debug=True)

