import pytest
from app import app, db, Task


@pytest.fixture
def client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_get_tasks_returns_empty_list_initially(client):
    response = client.get('/tasks')
    assert response.status_code == 200
    assert response.json == []


def test_post_tasks_creates_new_task(client):
    response = client.post('/tasks', json={'title': 'Buy milk'})
    assert response.status_code == 201
    assert response.json['title'] == 'Buy milk'
    assert response.json['done'] == False
    assert 'id' in response.json


def test_get_tasks_returns_created_task(client):
    client.post('/tasks', json={'title': 'Test task'})

    response = client.get('/tasks')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['title'] == 'Test task'
    assert response.json[0]['done'] == False


def test_delete_task_removes_task(client):
    create_response = client.post('/tasks', json={'title': 'Task to delete'})
    task_id = create_response.json['id']

    delete_response = client.delete(f'/tasks/{task_id}')
    assert delete_response.status_code == 200

    get_response = client.get('/tasks')
    assert get_response.json == []