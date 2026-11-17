from ckan.plugins import toolkit as tk


def get_comment_thread(dataset_name):
    url = '/dataset/%s' % dataset_name
    return tk.get_action('thread_show')(
        {'with_deleted': False}, {'url': url})


def get_site_captcha():
    return tk.config.get("ckan.captcha_siteid")


def get_helpers():
    return {
        'get_comment_thread': get_comment_thread,
        'get_site_captcha': get_site_captcha,
    }
