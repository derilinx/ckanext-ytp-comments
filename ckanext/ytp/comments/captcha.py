import logging
import os

import requests
from flask import has_request_context

import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

CAPTCHA_API_URL = 'https://www.google.com/recaptcha/api/siteverify'


def _check_captcha(response):
    if not response:
        return False
    params = {
        'secret': tk.config.get('ckan.captcha_secret'),
        'response': response
    }
    try:
        res = requests.post(CAPTCHA_API_URL, params=params, timeout=10)
        data = res.json()
    except (requests.RequestException, ValueError):
        log.exception('Error checking the captcha')
        return False
    # response: {success: true|false, error-codes: [...]
    # https://developers.google.com/recaptcha/docs/verify
    log.debug('captcha response: %s', data)
    return data.get('success', False)


def check():
    """Check the captcha of the current request if running in production.

    Requests without a valid `g-recaptcha-response` value (including API
    calls) are rejected. Calls made outside a web request (e.g. from the CLI)
    are not checked.

    :raises: ValidationError if the captcha is not valid
    """
    if os.environ.get('PRODUCTION', None) != 'true':
        return
    if not has_request_context():
        return

    if not _check_captcha(tk.request.form.get('g-recaptcha-response')):
        raise tk.ValidationError(
            {'captcha': [tk._('You failed to enter a valid captcha')]})
