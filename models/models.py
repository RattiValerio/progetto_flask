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

    # 'id': self.id,
    # 'latitude': self.latitude,
    # 'longitude': self.longitude,
    # 'muzzle_speed': self.muzzle_speed,
    # 'vertical_angle': self.vertical_angle,
    # 'horizontal_angle': self.horizontal_angle,
    # 'projectile_weight': self.projectile_weight,
    # 'timestamp': self.timestamp,
    # 'sender': self.sender,
    def to_dict(self):
        return {
            'request': {
                'id': self.id,
                'latitude': self.latitude,
                'longitude': self.longitude,
                'muzzle_speed': self.muzzle_speed,
                'vertical_angle': self.vertical_angle,
                'horizontal_angle': self.horizontal_angle,
                'projectile_weight': self.projectile_weight,
                'timestamp': self.timestamp,
                'sender': self.sender,
            },
            'response': self.response.to_dict()
        }


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

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'final_position': {
                'latitude': self.final_position_lat,
                'longitude': self.final_position_lon,
                'altitude': self.final_position_alt
            },
            'horizontal_distance': self.horizontal_distance,
            'max_height': self.max_height,
            'max_height_relative': self.max_height_relative,
            'flight_time': self.flight_time
        }