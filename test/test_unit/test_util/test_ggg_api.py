from pytest import mark
from app.util.ggg_api import RateLimiter


@mark.parametrize('state_header,expected', [('1:60:0,1:1800:0,1:7200:0', 0),
                                            ('10:60:0,5:1800:0,179:7200:0', 41),
                                            ('1:60:999,1:1800:0,179:7200:0', 999),
                                            ('1:60:0,89:1800:0,1:7200:0', 21)])
def test_rate_limiter_parse_headers_returns_longest_wait_time(state_header, expected):
    headers = {
        'X-Rate-Limit-Ip': '15:60:120,90:1800:600,180:7200:3600',
        'X-Rate-Limit-Ip-State': state_header
    }
    rl = RateLimiter()
    assert rl.parse_headers(headers) == expected


def test_rate_limiter_stop_or_go_returns_0_if_requests_remain():
    l_interval = '15:60:120'
    s_interval = '1:60:0'

    rl = RateLimiter()
    assert rl._stop_or_go(l_interval, s_interval) == 0


def test_rate_limiter_stop_or_go_returns_state_blackout_interval():
    s_blackout = 10

    l_interval = '15:60:120'
    s_interval = f'1:60:{s_blackout}'

    rl = RateLimiter()
    assert rl._stop_or_go(l_interval, s_interval) == s_blackout


def test_rate_limiter_stop_or_go_returns_wait_time_if_close_to_blackout():
    l_interval = '60:60:120'
    s_interval = '59:60:0'

    rl = RateLimiter()
    assert rl._stop_or_go(l_interval, s_interval) > 0


def test_rate_limiter_stop_or_go_wait_time_based_on_request_rate_limit():
    l_interval = '30:60:120'
    s_interval = '29:60:0'

    rl = RateLimiter()
    assert rl._stop_or_go(l_interval, s_interval) == 2 + 1
