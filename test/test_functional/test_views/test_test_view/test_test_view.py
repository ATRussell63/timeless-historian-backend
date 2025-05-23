
def test_test_view(test_app):
    response = test_app.post('/test').json[0]

    assert response['results']