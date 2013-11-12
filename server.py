import hashlib
import os

from flask import abort, Flask, redirect, render_template, request, url_for
from pymongo import MongoClient


MONGO_URL = os.environ.get('MONGOHQ_URL', 'mongodb://127.0.0.1:27017/shortner')
conn = MongoClient(MONGO_URL)
db = conn[MONGO_URL.split('/')[-1]]

SERVER_URL = os.environ.get('SERVER_URL', '127.0.0.1:5000')
app = Flask(__name__)


def base_52(num, power=6, result=''):

    if power < 0:
        return result

    if power > 5:
        return base_52(num % pow(52, power), power - 1)

    value = num / pow(52, power)

    if value < 26:
        c = chr(value + 65)
    else:
        c = chr(value + 71)

    return base_52(num % pow(52, power), power - 1, result = result + c)


def shorten_url(url):
    m = hashlib.md5()
    m.update(url)
    path = base_52(int(m.hexdigest(), 16))
    return (path, '%s/%s' % (SERVER_URL, path))


@app.route("/")
def index_handler():
    return redirect(url_for('create_handler'))


@app.route("/create")
def create_handler():
    url = request.args.get('url')
    short_url = None

    if url is not None:
        path, short_url = shorten_url(url)
        db.links.save({'_id': path, 'url': url})

    return render_template('create.html', short_url=short_url)


@app.route("/<path>")
def short_handler(path):
    result = db.links.find_one({'_id': path})

    if result is None:
        return abort(404)

    return redirect(result['url'], 301)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
