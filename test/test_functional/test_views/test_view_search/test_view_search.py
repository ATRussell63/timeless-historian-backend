from pytest import mark


def test_search_mf(test_app):
    body = {
        'jewel_type': 'Militant Faith',
        'seed': 7875,
        'general': 'Dominus',
        'mf_mods': ['1% reduced Mana Cost of Skills per 10 Devotion',
                    '+2% to all Elemental Resistances per 10 Devotion']
    }

    response = test_app.post('/search', json=body).json
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

    response = test_app.post('/search', json=body).json
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

    response = test_app.post('/search', json=body).json
    assert response['results']['Settlers'][0]['mf_mods_match_count'] == 0


def test_search_mf_1_mf_match(test_app):
    body = {
        'jewel_type': 'Militant Faith',
        'seed': 8076,
        'general': 'Dominus',
        'mf_mods': ['4% increased Totem Damage per 10 Devotion',
                    '4% increased Brand Damage per 10 Devotion']
    }

    response = test_app.post('/search', json=body).json
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

    response = test_app.post('/search', json=body).json
    assert response['results']
    assert response['results']['Settlers'][0]['mf_mods_match_count'] == 2
    assert set([response['results']['Settlers'][0]['mf_mod_1'], response['results']['Settlers'][0]['mf_mod_2']]) == set(mods)


def test_search_non_mf(test_app):
    body = {
        'jewel_type': 'Lethal Pride',
        'seed': 14435,
        'general': 'Doryani'
    }

    response_body = test_app.post('/search', json=body).json
    assert response_body['results']['Settlers'][0]['character_name'] == 'NeedForSteveUnderground'


# bulk tests were run on jul 16 backup data

@mark.parametrize('jewel_type, seed, general, expected_seed_match, expected_general_match',
                  [('Lethal Pride', 15231, 'Rakiata', 18, 7),
                   ('Elegant Hubris', 139520, 'Cadiro', 18, 5),
                   ('Brutal Restraint', 5924, 'Asenath', 17, 5),
                   ('Glorious Vanity', 2535, 'Xibaqua', 8, 3)])
def test_search_bulk_single__non_MF(test_app, jewel_type, seed, general, expected_seed_match, expected_general_match):
    i = 0
    x = 8
    y = 12
    mf_mods = None

    body = {
        'jewels': [
            {
                'i': i,
                'x': x,
                'y': y,
                'jewel_type': jewel_type,
                'seed': seed,
                'general': general,
                'mf_mods': mf_mods
            }
        ]
    }

    response_body = test_app.post('/search/bulk', json=body).json
    jewel_row = response_body['results'][0]
    assert jewel_row['i'] == i
    assert jewel_row['x'] == x
    assert jewel_row['y'] == y
    assert jewel_row['seed_match'] == expected_seed_match
    assert jewel_row['general_match'] == expected_general_match
    assert jewel_row['exact_match'] == expected_general_match


def test_search_bulk_single_MF(test_app):
    i = 0
    x = 8
    y = 12
    jewel_type = 'Militant Faith'
    seed = 7677
    general = 'Dominus'
    mf_mods = ['Regenerate 0.6 Mana per Second per 10 Devotion',
               '3% increased Effect of non-Damaging Ailments on Enemies per 10 Devotion']

    body = {
        'jewels': [
            {
                'i': i,
                'x': x,
                'y': y,
                'jewel_type': jewel_type,
                'seed': seed,
                'general': general,
                'mf_mods': mf_mods
            }
        ]
    }

    response_body = test_app.post('/search/bulk', json=body).json
    jewel_row = response_body['results'][0]
    assert jewel_row['i'] == i
    assert jewel_row['x'] == x
    assert jewel_row['y'] == y
    assert jewel_row['seed_match'] == 4
    assert jewel_row['general_match'] == 4
    assert jewel_row['exact_match'] == 0


def test_search_bulk_multiple(test_app):
    body = {
        'jewels': [
            {
                'i': 0,
                'x': 0,
                'y': 0,
                'jewel_type': 'Lethal Pride',
                'seed': 15231,
                'general': 'Rakiata',
                'mf_mods': None
            },
            {
                'i': 1,
                'x': 0,
                'y': 1,
                'jewel_type': 'Elegant Hubris',
                'seed': 139520,
                'general': 'Cadiro',
                'mf_mods': None
            },
            {
                'i': 2,
                'x': 0,
                'y': 2,
                'jewel_type': 'Brutal Restraint',
                'seed': 5924,
                'general': 'Asenath',
                'mf_mods': None
            },
            {
                'i': 3,
                'x': 0,
                'y': 3,
                'jewel_type': 'Glorious Vanity',
                'seed': 2535,
                'general': 'Xibaqua',
                'mf_mods': None
            },
            {
                'i': 4,
                'x': 0,
                'y': 4,
                'jewel_type': 'Militant Faith',
                'seed': 7677,
                'general': 'Dominus',
                'mf_mods': ['Regenerate 0.6 Mana per Second per 10 Devotion',
                            '3% increased Effect of non-Damaging Ailments on Enemies per 10 Devotion']
            },
        ]
    }

    expected_matches = [
        {
            'seed': 18,
            'general': 7,
            'exact': 7 
        },
        {
            'seed': 18,
            'general': 5,
            'exact': 5 
        },
        {
            'seed': 17,
            'general': 5,
            'exact': 5 
        },
        {
            'seed': 8,
            'general': 3,
            'exact': 3 
        },
        {
            'seed': 4,
            'general': 4,
            'exact': 0 
        },
    ]

    response_body = test_app.post('/search/bulk', json=body).json
    jewel_rows = response_body['results']

    for i, row in enumerate(jewel_rows):
        assert row['seed_match'] == expected_matches[i]['seed']
        assert row['general_match'] == expected_matches[i]['general']
        assert row['exact_match'] == expected_matches[i]['exact']