from flask import Flask, url_for, render_template
from blueprints.api import app as api_app

app = Flask(__name__)

app.register_blueprint(api_app, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
