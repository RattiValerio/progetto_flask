from flask import Flask, url_for, render_template
from blueprints.api import app as api_app
from models.conn import db
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ballistics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # added to avoid circular import
# Configurazione di Flask-Migrate
migrate = Migrate(app, db)

from models.models import Request
from models.models import Response

app.register_blueprint(api_app, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
