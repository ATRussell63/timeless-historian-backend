

def test_data_summary(test_app):
    response = test_app.get('/data/summary').json[0]
    assert response