from datetime import datetime

from models.conn import db

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.String, nullable=False)
    longitude = db.Column(db.String, nullable=False)
    muzzle_speed = db.Column(db.Float, nullable=False)
    vertical_angle = db.Column(db.Float, nullable=False)
    horizontal_angle = db.Column(db.Float, nullable=False)
    projectile_weight = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())
    sender = db.Column(db.String, nullable=False)

    response = db.relationship('Response', backref='request', uselist=False)


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    final_position_lat = db.Column(db.Float, nullable=False)
    final_position_lon = db.Column(db.Float, nullable=False)
    final_position_alt = db.Column(db.Float, nullable=False)
    horizontal_distance = db.Column(db.Float, nullable=False)
    max_height = db.Column(db.Float, nullable=False)
    max_height_relative = db.Column(db.Float, nullable=False)
    flight_time = db.Column(db.Integer, nullable=False)