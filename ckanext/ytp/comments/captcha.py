import requests
import os

import ckan.plugins.toolkit as tk
config = tk.config

CAPTCHA_API_URL = 'https://www.google.com/recaptcha/api/siteverify'

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _check_captcha(response):
    if not response:
        return False
    params = {
        'secret': config.get('ckan.captcha_secret'),
        'response': response
    }
    res = requests.post(CAPTCHA_API_URL, params=params)
    data = res.json()
    # response: {success: true|false, error-codes: [...]
    # https://developers.google.com/recaptcha/docs/verify
    logger.debug('captcha response: %s' % data)
    return data.get('success', False)


def check(request, c):
    """ Check the captcha if config is enabled.

    side effects -- returns in c

    :param: request the request object
    :param: c context error dict
    """

    if os.environ.get('PRODUCTION', None) == 'true':
        answer = _check_captcha(request.POST.get('g-recaptcha-response', None))
        if not answer:
            c.errors['Captcha Failure'] = ['You failed to enter a valid captcha']
            c.errors_summary['Captcha Failure'] = 'You failed to enter a valid captcha'