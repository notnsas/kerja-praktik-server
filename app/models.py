from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db


class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[int] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    posts: so.WriteOnlyMapped["Post"] = so.relationship(back_populates="author")

    def __repr__(self):
        return "<User is{}".format(self.username)


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates="posts")

    def __repr__(self):
        return "<Post {}>".format(self.body)


class Hotel(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(140))
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    rating: so.Mapped[Optional[float]] = so.mapped_column(sa.Float)
    image_link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    def __repr__(self):
        return "<Hotel {}>".format(self.name)


class Room(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(140))
    property_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Hotel.id), index=True)

    def __repr__(self):
        return "<Room {}>".format(self.name)
