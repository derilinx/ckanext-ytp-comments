import logging

from flask import Blueprint

from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)

blueprint = Blueprint('comments', __name__)

MAX_WORDS = 300


def _get_dataset(dataset_id):
    try:
        return tk.get_action('package_show')({}, {'id': dataset_id})
    except tk.ObjectNotFound:
        return tk.abort(404, tk._('Dataset not found'))
    except tk.NotAuthorized:
        return tk.abort(403, tk._('Not authorized to see this dataset'))


def _redirect_to_dataset(dataset, comment_id=None):
    url = tk.h.url_for('dataset.read', id=dataset['name'])
    if comment_id:
        url += '#comment_%s' % comment_id
    return tk.redirect_to(url)


def _error_message(error):
    return ' '.join(
        '; '.join(msgs) if isinstance(msgs, list) else str(msgs)
        for msgs in error.error_dict.values()
    )


@blueprint.route('/dataset/<dataset_id>/comments/add', methods=['POST'])
def add(dataset_id):
    return _add_or_reply(dataset_id)


@blueprint.route(
    '/dataset/<dataset_id>/comments/<parent_id>/reply', methods=['POST'])
def reply(dataset_id, parent_id):
    return _add_or_reply(dataset_id, parent_id)


def _add_or_reply(dataset_id, parent_id=None):
    """
    Allows the user to add a comment to an existing dataset
    """

    # First, kill any spam in the honeypot fields
    if tk.request.form.get('comment-email') or \
            tk.request.form.get('comment-url'):
        log.error("SPAM post rejected w/email,url: %s", tk.request.form)
        return tk.abort(403, tk._('You failed to enter a valid captcha'))

    dataset = _get_dataset(dataset_id)

    body = tk.request.form.get('comment', '')
    if not body.strip():
        tk.h.flash_error(tk._('You must provide a comment body'))
        return _redirect_to_dataset(dataset)

    if len(body.split()) > MAX_WORDS:
        tk.h.flash_error(
            tk._('Please limit your comment to {} words').format(MAX_WORDS))
        return _redirect_to_dataset(dataset)

    data_dict = {
        'url': '/dataset/%s' % dataset['name'],
        'subject': tk.request.form.get('subject', ''),
        'comment': body,
        'parent_id': parent_id,
    }
    try:
        comment = tk.get_action('comment_create')({}, data_dict)
    except tk.NotAuthorized:
        return tk.abort(403, tk._('Not authorized to add comments'))
    except tk.ValidationError as e:
        tk.h.flash_error(_error_message(e))
        return _redirect_to_dataset(dataset)

    return _redirect_to_dataset(dataset, comment['id'])


@blueprint.route(
    '/dataset/<dataset_id>/comments/<comment_id>/edit', methods=['POST'])
def edit(dataset_id, comment_id):
    dataset = _get_dataset(dataset_id)

    data_dict = {
        'id': comment_id,
        'subject': tk.request.form.get('subject', ''),
        'comment': tk.request.form.get('comment', ''),
    }
    try:
        comment = tk.get_action('comment_update')({}, data_dict)
    except tk.NotAuthorized:
        return tk.abort(403, tk._('Not authorized to edit this comment'))
    except tk.ObjectNotFound:
        return tk.abort(404, tk._('Comment not found'))
    except tk.ValidationError as e:
        tk.h.flash_error(_error_message(e))
        return _redirect_to_dataset(dataset)

    return _redirect_to_dataset(dataset, comment['id'])


@blueprint.route(
    '/dataset/<dataset_id>/comments/<comment_id>/delete', methods=['POST'])
def delete(dataset_id, comment_id):
    dataset = _get_dataset(dataset_id)

    try:
        tk.get_action('comment_delete')({}, {'id': comment_id})
    except tk.NotAuthorized:
        return tk.abort(403, tk._('Not authorized to delete this comment'))
    except tk.ObjectNotFound:
        return tk.abort(404, tk._('Comment not found'))

    return _redirect_to_dataset(dataset)
