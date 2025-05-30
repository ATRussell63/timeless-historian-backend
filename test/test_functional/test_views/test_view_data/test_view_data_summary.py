from pytest import mark


def test_view_data_summary(test_app):
    response = test_app.get('/data/summary').json
    assert response['results']['total_characters']
    assert response['results']['total_jewels']
    assert response['results']['unique_jewels']
    assert response['results']['unique_seeds']


@mark.parametrize('limit', [-1, 100])
def test_view_data_sample_rejects_out_of_bounds_limit(test_app, limit):
    response = test_app.get(f'/data/sample?limit={limit}')
    assert response.status_code == 400


def test_view_data_sample_returns_requested_size_sample(test_app):
    limit = 10
    response = test_app.get(f'/data/sample?limit={limit}').json
    
    count = 0
    for league_name, league in response['results'].items():
        count += len(league['jewels'])
    
    assert count == limit