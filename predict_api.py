import sqlalchemy as sa
import sqlalchemy.orm as so
from app import app, db
from app.models import User, Post, Hotel, Room


@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "so": so,
        "db": db,
        "User": User,
        "Post": Post,
        "Hotel": Hotel,
        "Room": Room,
    }


app.run(host="0.0.0.0", port=10000, debug=True)
