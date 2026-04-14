from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import boto3
import json
import sys
import time
import signal
import random

app = Flask(__name__)
CORS(app)

def get_secret():
    secret_name = os.environ.get('SECRET_NAME')
    region = os.environ.get('AWS_REGION', 'eu-north-1')
    
    client = boto3.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

secret_name = os.environ.get('SECRET_NAME')
if secret_name:
    credentials = get_secret()
    DB_USER = credentials['username']
    DB_PASSWORD = credentials['password']
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'todo_db')
else:
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'todo_db')
    
FAILURE_MODE = 'health_fail'
if FAILURE_MODE == 'crash':
    os.kill(os.getppid(), signal.SIGTERM)

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    done = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "done": self.done}

with app.app_context():
    db.create_all()

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if FAILURE_MODE == 'health_fail':
        return jsonify({"error": "application not responding"}), 500
    if FAILURE_MODE == 'application_error':
        failure_threshold = 0.8
        random_value = random.random()
        if random_value > failure_threshold:
            return jsonify({"error": "application not responding"}), 500
    tasks = Task.query.all()
    return jsonify([t.to_dict() for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    task = Task(title=data['title'])
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/api/tasks/<int:id>', methods=['PATCH'])
def toggle_task(id):
    task = Task.query.get(id)
    if not task:
        return jsonify({"error": "Not found"}), 404
    task.done = not task.done
    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = db.session.get(Task, id)
    if not task:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route('/api/ready', methods=['GET'])
def ready_check():
    if FAILURE_MODE == 'health_fail':
        return jsonify({"status": "not ready", "database": "disconnected"}), 503
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "ready", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "database": "disconnected"}), 503

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)