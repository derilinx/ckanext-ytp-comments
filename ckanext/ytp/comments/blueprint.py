from ckan.logic import check_access, get_action, clean_dict, tuplize_dict, ValidationError, parse_params
from ckan.lib.navl.dictization_functions import unflatten
from ckan.plugins import toolkit

from flask import Blueprint, request

blueprint = Blueprint('comments', __name__)

@blueprint.route('/dataset/<dataset_id>/comments/add', methods=["POST"])
def add(dataset_id):
    return _add_or_reply(dataset_id)

@blueprint.route('/dataset/<dataset_id>/comments/<comment_id>/edit', methods=["POST"])
def edit(dataset_id, comment_id):
    context = {}
    # Auth check to make sure the user can see this package

    check_access('package_show', context, {'id': dataset_id})

    pkg_dict = get_action('package_show')(context, {'id': dataset_id})


    data_dict = clean_dict(unflatten(tuplize_dict(parse_params(request.form))))
    data_dict['id'] = comment_id

    res = get_action('comment_update')(context, data_dict)
    return toolkit.redirect_to('/dataset/%s#comment_%s' % (pkg_dict['name'], res['id']))


@blueprint.route('/dataset/<dataset_id>/comments/<parent_id>/reply', methods=["POST"])
def reply(dataset_id, parent_id):
    return _add_or_reply(dataset_id, parent_id)

def _add_or_reply(dataset_id, parent=None):
    """
    Allows the user to add a comment to an existing dataset
    """

    # First, kill any spam in the honeypot fields
    if request.form.get('comment-email', False) or \
            request.form.get('comment-url', False):
        log.error("SPAM post rejected w/email,url: %s", request.form)
        toolkit.abort(403, 'You failed to enter a valid captcha')

    context = {}

    # Auth check to make sure the user can see this package
    check_access('package_show', context, {'id': dataset_id})

    pkg = get_action('package_show')(context, {'id': dataset_id})

    data_dict = clean_dict(unflatten(tuplize_dict(parse_params(request.form))))
    data_dict['parent_id'] = parent
    data_dict['url'] = '/dataset/%s' % pkg['name']

    body = data_dict.get('comment', False)
    if not body:
        h.flash_error('You must provide a comment body')
        h.redirect_to('package.read', id=dataset_id)

    words = data_dict.get('comment', '').split(' ')
    if len(words) > 300:
        h.flash_error('Please limit your comment to 300 words')
        h.redirect_to('package.read', id=dataset_id)

    res = get_action('comment_create')(context, data_dict)
    return toolkit.redirect_to('/dataset/%s#comment_%s' % (pkg['name'], res['id']))

@blueprint.route('/dataset/<dataset_id>/comments/<comment_id>/delete', methods=["GET", "POST", "DELETE"])
def delete(dataset_id, comment_id):
    context = {}

    # Auth check to make sure the user can see this package
    check_access('package_show', context, {'id': dataset_id})

    get_action('comment_delete')(context, {'id': comment_id})

    return toolkit.redirect_to('/dataset/%s' % dataset_id)