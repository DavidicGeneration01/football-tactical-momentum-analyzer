from src.main import app


def test_main_exports_wsgi_app():
    assert callable(app)
