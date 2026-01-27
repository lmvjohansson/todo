import pytest
from app import app, db, Task
from sqlalchemy import inspect


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


def test_database_connection_established(client):
    with app.app_context():
        result = db.session.execute(db.text('SELECT 1'))
        assert result.scalar() == 1


def test_database_schema_initialized_correctly(client):
    with app.app_context():
        inspector = inspect(db.engine)

        assert 'task' in inspector.get_table_names()

        columns = {col['name']: col['type'] for col in inspector.get_columns('task')}

        assert 'id' in columns
        assert 'title' in columns
        assert 'done' in columns

        assert str(columns['title'].python_type) == "<class 'str'>"
        assert str(columns['done'].python_type) == "<class 'bool'>"