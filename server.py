import datetime
import hashlib
import os

from flask import abort, Flask, redirect, render_template, request, url_for
from pymongo import MongoClient


MONGO_URL = os.environ.get('MONGOHQ_URL', 'mongodb://127.0.0.1:27017/shortener')
conn = MongoClient(MONGO_URL)
db = conn[MONGO_URL.split('/')[-1]]

SERVER_URL = os.environ.get('SERVER_URL', '127.0.0.1:5000')
app = Flask(__name__)


def base_61(num, power=6, result=''):

    if power < 0:
        return result

    if power > 5:
        return base_61(num % pow(61, power), power - 1)

    value = num / pow(61, power)

    if value < 26:
        c = chr(value + 65)
    elif value < 52:
        c = chr(value + 71)
    else:
        c = chr(value - 3)

    return base_61(num % pow(61, power), power - 1, result = result + c)


def shorten_url(url):
    m = hashlib.md5()
    m.update(url)
    path = base_61(int(m.hexdigest(), 16))
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

        if db.links.find_one({'_id': path}) is None:
            db.links.save({'_id': path, 'url': url, 'hits': []})

    return render_template('create.html', url=url, short_url=short_url)


@app.route("/<path>")
def link_handler(path):
    link = db.links.find_one({'_id': path});

    if link is None:
        return abort(404)

    link['hits'].append({
        'timestamp': datetime.datetime.now(),
        'host': request.host,
        'referrer': request.referrer,
        'browser': request.user_agent.browser,
        'language': request.user_agent.language,
        'platform': request.user_agent.platform,
        'version': request.user_agent.version
        })
    db.links.save(link)

    return redirect(link['url'], 301)


@app.route("/<path>+")
def stats_handler(path):
    link = db.links.find_one({'_id': path});

    if link is None:
        return abort(404)

    num_hits = len(link['hits'])

    return render_template('stats.html', path=path, num_hits=num_hits,
                           url=link['url'])


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
