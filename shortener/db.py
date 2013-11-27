from datetime import datetime
import os
from urlparse import urlparse

import psycopg2
import psycopg2.extras


class Db:

    def __init__(self):
        url = urlparse(os.getenv('DATABASE_URL'))

        self.conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def create_link(self, path, url):
        if self.get_link(path) is None:
            self.cur.execute("INSERT INTO links VALUES (%s, %s, %s)",
                             (path, url, datetime.now()))
            self.conn.commit()

    def get_link(self, path):
        self.cur.execute("SELECT * FROM links WHERE path = %s", (path,))
        return self.cur.fetchone()

    def hit_link(self, path, referrer=None, browser=None, platform=None, version=None):
        self.cur.execute(
            "INSERT INTO hits VALUES (%s, %s, %s, %s, %s, %s)",
            (path, datetime.now(), referrer, browser, platform, version)
            )
        self.conn.commit()

    def get_hits(self, path):
        self.cur.execute("SELECT * FROM hits WHERE path = %s", (path,))
        return self.cur.fetchall()


db = Db()
