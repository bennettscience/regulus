import json
import os
from sqlalchemy import Table


class Loader(object):
    """
    Reusable class for loading fixture data into test databases.

    Initialize with an in-context application and database engine.
    """

    def __init__(self, app, db, fixtures):
        self.app = app
        self.connection = db.engine.connect()
        self.fixtures = fixtures
        self.metadata = db.metadata

    def load(self):
        for filename in self.fixtures:
            filepath = os.path.join(self.app.config["FIXTURES_DIR"], filename)
            with open(filepath) as file_in:
                self.data = json.load(file_in)
                self.load_from_file()

    def load_from_file(self):
        table = Table(self.data[0]["table"], self.metadata)
        self.connection.execute(table.insert(), self.data[0]["records"])
        return
