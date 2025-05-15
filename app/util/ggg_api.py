import logging
import requests
import time
from math import ceil
from requests import Response
from requests.exceptions import HTTPError

from app.app_config import get_config
from app.util.exceptions import PrivateAccountException

logger = logging.getLogger('main')


class RateLimiter():

    def __init__(self):
        pass

    def parse_headers(self, headers: dict) -> int:
        limit_intervals = headers['X-Rate-Limit-Ip'].split(',')
        state_intervals = headers['X-Rate-Limit-Ip-State'].split(',')

        assert len(limit_intervals) == len(state_intervals)

        wait = 0
        for x in range(len(limit_intervals)):
            interval_wait = self._stop_or_go(limit_intervals[x], state_intervals[x])
            wait = interval_wait if interval_wait > wait else wait

        if wait > 0:
            logger.debug(f'Headers indicate we should pause for {wait} seconds.')

        return wait

    def _stop_or_go(self, limit_interval: str, state_interval: str) -> int:
        l_requests, l_interval_len, l_blackout = (int(s) for s in limit_interval.split(':'))
        s_requests, s_interval_len, s_blackout = (int(s) for s in state_interval.split(':'))

        if s_blackout > 0:
            logger.error(f'Blacked out on {s_interval_len} second interval. \
                         Signaling to pause for {s_blackout} seconds.')
            return s_blackout

        elif s_requests >= l_requests - 1:
            interval_rate_limit = ceil(int(l_interval_len / l_requests)) + 1
            logger.debug(f'Reached {s_requests} of maximum {l_requests} requests on {s_interval_len} second interval. \
                         Signaling to pause for {interval_rate_limit} seconds')
            return interval_rate_limit

        else:
            return 0


class Endpoint():

    def __init__(self, url):
        self.url = url
        self._rate_limiter = RateLimiter()

    def get(self, params: dict, fmt_args: dict = None) -> Response:
        if '{' in self.url:
            url = self.url.format(**fmt_args)
        else:
            url = self.url

        headers = {
            'User-Agent': 'application/json'
        }

        response = requests.get(url, params=params, headers=headers)
        wait_time = self._rate_limiter.parse_headers(response.headers)
        self.wait(wait_time)
        return response

    def wait(self, seconds: int):
        logger.debug(f'Pausing for {seconds} seconds...')
        time.sleep(seconds)
        logger.debug('Back to work!')


class GGG_Api():

    def __init__(self):
        self.ENDPOINTS = {
            'get-passive-skills': Endpoint(get_config().SITE_BASE_URL + '/character-window/get-passive-skills'),
            # 'ladder': Endpoint(get_config().SITE_BASE_URL + '/league/{league_name}/ladder'),
            'ladder': Endpoint(get_config().SITE_BASE_URL + '/api/ladders'),
            'league': Endpoint(get_config().SITE_BASE_URL + '/league')
        }

    def rate_limited_get(self, endpoint: Endpoint, params: dict, url_fmt_args: dict = None) -> Response:
        try:
            response = endpoint.get(params, url_fmt_args)
            response.raise_for_status()
        except HTTPError as e:
            if response.status_code == 429:
                logger.error('Error code 429 received. Retrying...')
                response = endpoint.get(params)
                response.raise_for_status()
            else:
                logger.error(f'Unexpected error from GET against {endpoint.url} - Error: {e}')
                raise e

        return response

    def get_passive_skills(self, account_name: str, character_name: str, realm: str = 'pc') -> Response:

        params = {
            'accountName': account_name,
            'character': character_name,
            'realm': realm
        }

        try:
            response = self.rate_limited_get(self.ENDPOINTS['get-passive-skills'], params)
        except HTTPError as e:
            if '403' in str(e):
                raise PrivateAccountException(str(e))
        return response

    def get_ladder_chunk(self, league_name: str, limit_max: int, offset_coeff: int) -> Response:

        # params = {
        #     'sort': 'xp',
        #     'limit': limit_max,
        #     'offset': offset_coeff * limit_max,
        # }

        # url_fmt = {
        #     'league_name': league_name
        # }

        params = {
            'id': league_name,
            'limit': limit_max,
            'realm': 'pc',
            'type': 'league',
            'offset': offset_coeff * limit_max
        }

        # response = self.rate_limited_get(self.ENDPOINTS['ladder'], params, url_fmt)
        response = self.rate_limited_get(self.ENDPOINTS['ladder'], params)
        return response

    def get_leagues(self):

        params = {
            'type': 'main'
        }

        response = self.rate_limited_get(self.ENDPOINTS['league'], params)
        return response
