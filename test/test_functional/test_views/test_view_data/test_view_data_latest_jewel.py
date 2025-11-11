
def test_view_data_latest_jewel(test_app):
    response = test_app.get('/data/latest').json
    assert len(response['results']) == 1
    league = next(iter(response['results']))
    assert len(response['results'][league]['jewels']) == 1