import os

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
# app = Flask(
#     __name__,
#     template_folder="../dist",  # Path to dist folder
#     static_folder="",  # Path to static subfolder
# )
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"Root directory: {ROOT_DIR}")
# from app import routes
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models
