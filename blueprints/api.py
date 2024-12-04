import math

from flask import render_template, url_for, Blueprint, request, jsonify

app = Blueprint('api', __name__)


@app.route('/data', methods=['GET'])
def get_data():
    query_param = request.args.get('param')
    response = {
        'message': 'Received GET request',
        'param': query_param
    }
    return jsonify(response), 200


@app.route('/calculate/projectile_ballistics', methods=['POST'])
def calculate_projectile_ballistics():
    #pos = request.form.get('starting_position')

    x = 0 #request.form.get('x')
    y = 0 #request.form.get('y')
    z = 0 #request.form.get('z')

    v0 = 800 #request.form.get('muzzle_speed')

    vertical_angle = 45 #request.form.get('vertical_angle')
    horizontal_angle = 80 #request.form.get('horizontal_angle')

    m = 43 #request.form.get('projectile_weight')

    g = 9.81

    # x = v0x * t
    # y = v0y *t - 1/2 * g * t ^ 2

    # Velocità iniziali
    # v0x = v0 * cos(angolo_verticale) * cos(angolo_orizzontale)
    # v0z = v0 * cos(angolo_verticale) * sin(angolo_orizzontale)
    # v0y = v0 * sin(angolo_verticale)

    v0x = v0 * math.cos(vertical_angle) * math.cos(horizontal_angle)
    v0z = v0 * math.cos(vertical_angle) * math.sin(horizontal_angle)
    v0y = v0 * math.sin(vertical_angle)

    # Tempo di volo
    # y0 + v0y * t - 1/2 * g * t ^ 2
    # tf = (2 * v0y) / g

    tf = (2 * v0y) / g

    # Posizione finale
    # xf = x0 + v0 * cos(angolo_verticale) * cos(angolo_orizzontale) * tf
    # zf = z0 + z0 * cos(angolo_verticale) * sin(angolo_orizzontale) * tf
    # yf = y0 ???

    xf = x + v0x * tf
    zf = z + v0z * tf
    yf = y

    # Altezza massima
    # ymax = y0 + ((v0 * sin(angolo_verticale)) ^ 2) / 2 * g

    ymax = y + (v0y * v0y) / (2 * g)


    response = {
        'final_position':{
            'X': xf,
            'Y': yf,
            'Z': zf
        },
        'fly_time': tf,
        'max_height': ymax
    }
    return jsonify(response), 201


@app.route('/update/<int:id>', methods=['PUT'])
def update_data(id):
    updated_data = request.json
    response = {
        'message': 'Received PUT request',
        'id': id,
        'updated_data': updated_data
    }
    return jsonify(response), 200


@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_data(id):
    response = {
        'message': 'Received DELETE request',
        'id': id,
        'status': 'Resource deleted'
    }
    return jsonify(response), 200
