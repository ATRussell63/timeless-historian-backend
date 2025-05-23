

def test_search_mf(test_app):
    body = {
        'jewel_type': 'Militant Faith',
        'seed': 7875,
        'general': 'Dominus',
        'mf_mods': ['1% reduced Mana Cost of Skills per 10 Devotion',
                    '+2% to all Elemental Resistances per 10 Devotion']
    }

    response = test_app.post('/search', json=body).json[0]
    assert response['results']
    assert response['results']['Settlers']


def test_search_mf_wizi(test_app):
    body = {
        'jewel_type': 'Militant Faith',
        'seed': 8076,
        'general': 'Dominus',
        'mf_mods': ['4% increased Totem Damage per 10 Devotion',
                    '4% increased Elemental Damage per 10 Devotion']
    }

    response = test_app.post('/search', json=body).json[0]
    assert response['results']
    assert response['results']['Settlers'][0]['character_name'] == 'wizicypau'


def test_search_mf_0_mf_match(test_app):
    body = {
        'jewel_type': 'Militant Faith',
        'seed': 8076,
        'general': 'Dominus',
        'mf_mods': ['Regenerate 0.6 Mana per Second per 10 Devotion',
                    '4% increased Brand Damage per 10 Devotion']
    }

    response = test_app.post('/search', json=body).json[0]
    assert response['results']['Settlers'][0]['mf_mods_match_count'] == 0


def test_search_mf_1_mf_match(test_app):
    body = {
        'jewel_type': 'Militant Faith',
        'seed': 8076,
        'general': 'Dominus',
        'mf_mods': ['4% increased Totem Damage per 10 Devotion',
                    '4% increased Brand Damage per 10 Devotion']
    }

    response = test_app.post('/search', json=body).json[0]
    assert response['results']['Settlers'][0]['mf_mods_match_count'] == 1


def test_search_mf_returns_mf_mods(test_app):
    mods = ['4% increased Totem Damage per 10 Devotion',
            '4% increased Elemental Damage per 10 Devotion']

    body = {
        'jewel_type': 'Militant Faith',
        'seed': 8076,
        'general': 'Dominus',
        'mf_mods': mods
    }

    response = test_app.post('/search', json=body).json[0]
    assert response['results']
    assert response['results']['Settlers'][0]['mf_mods_match_count'] == 2
    assert set([response['results']['Settlers'][0]['mf_mod_1'], response['results']['Settlers'][0]['mf_mod_2']]) == set(mods)


def test_search_non_mf(test_app):
    body = {
        'jewel_type': 'Lethal Pride',
        'seed': 14435,
        'general': 'Doryani'
    }

    response_body = test_app.post('/search', json=body).json[0]
    assert response_body['results']['Settlers'][0]['character_name'] == 'NeedForSteveUnderground'