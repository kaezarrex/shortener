import collections
import datetime
import hashlib
import os

from flask import abort, Flask, redirect, render_template, request

from shortener.db import db


SERVER_URL = os.environ.get('SERVER_URL', 'http://127.0.0.1:5000/')
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


def path_to_url(path):
    return '%s%s' % (SERVER_URL, path)


def shorten_url(url):
    m = hashlib.md5()
    m.update(url)
    path = base_61(int(m.hexdigest(), 16))
    return (path, path_to_url(path))


@app.route("/")
def index_handler():
    url = request.args.get('url')
    short_url = None

    if url is not None:
        path, short_url = shorten_url(url)

        db.create_link(path, url)

    return render_template('index.html', url=url, short_url=short_url)


@app.route("/<path>")
def link_handler(path):
    link = db.get_link(path)

    if link is None:
        return abort(404)

    db.hit_link(
        path,
        referrer=request.referrer,
        browser=request.user_agent.browser,
        platform=request.user_agent.platform,
        version=request.user_agent.version
        )

    return redirect(link['url'], 301)


@app.route("/<path>+")
def stats_handler(path):
    link = db.get_link(path)
    hits = db.get_hits(path)

    if link is None:
        return abort(404)

    day_labels = list()
    day_data = list()
    num_hits = len(hits)

    if num_hits:

        dates = (hit['timestamp'].date() for hit in hits)
        date_counter = collections.Counter(dates)
        current_date = min(date_counter)

        while current_date <= max(date_counter):
            day_labels.append(str(current_date))
            day_data.append(date_counter[current_date])
            current_date += datetime.timedelta(days=1)

    return render_template('stats.html', short_url=path_to_url(path),
                           url=link['url'], num_hits=num_hits,
                           day_labels=day_labels, day_data=day_data)


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
