import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir,
                                                                    "data_warehouse.db")
db = SQLAlchemy(app)

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
