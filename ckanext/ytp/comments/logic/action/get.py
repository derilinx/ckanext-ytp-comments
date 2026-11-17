from ckan import model
from ckan.plugins import toolkit as tk

import ckanext.ytp.comments.model as comment_model


@tk.side_effect_free
def thread_show(context, data_dict):
    """
    Returns the content of a thread, based on a url or id. If a url is
    provided and the thread does not exist, it will be created.

    :param url: the URL of the commented object, e.g. ``/dataset/<name>``
    :param id: the id of the thread

    Context options:

    with_deleted (boolean) - Also show deleted comments
    approved_only (boolean) - Only show approved comments
    offset (int) - The number of comments to offset in the threads comment list
    limit (int) - Total number of comments to return.
    """
    tk.check_access("thread_show", context, data_dict)

    url = data_dict.get('url')
    id = data_dict.get('id')
    thread = None
    if url:
        thread = comment_model.CommentThread.from_url(url)

    if not thread and id:
        thread = comment_model.CommentThread.get(id)

    if not thread:
        raise tk.ObjectNotFound(tk._('Thread not found'))

    # Dictize the thread and all the comments within it.
    thread_dict = thread.as_dict()
    # Add the top level comments from the thread in order to the
    # following list.
    comments = model.Session.query(comment_model.Comment). \
        filter(comment_model.Comment.thread_id == thread.id)

    # Add more filters based on whether we want comments of a certain state,
    # or spam comments etc.
    if context.get('approved_only') is True:
        comments = comments.filter(comment_model.Comment.approval_status ==
                                   comment_model.COMMENT_APPROVED)

    with_deleted = context.get('with_deleted') is True
    if not with_deleted:
        # TODO: Restrict to sysadmin
        comments = comments.filter(comment_model.Comment.state == 'active')

    # We only want the top-level comments because sub-comments will be
    # retrieved in the c.as_dict call
    comments = comments.filter(
        comment_model.Comment.parent_id == None)  # noqa: E711

    comments = comments.order_by(comment_model.Comment.creation_date.desc())

    if isinstance(context.get('offset'), int):
        comments = comments.offset(context['offset'])

    if isinstance(context.get('limit'), int):
        comments = comments.limit(context['limit'])

    thread_dict['comments'] = [
        c.as_dict(only_active_children=not with_deleted)
        for c in comments.all()
    ]

    return thread_dict


@tk.side_effect_free
def comment_show(context, data_dict):
    '''Return a comment, including its replies

    :param id: the id of the comment
    '''
    tk.check_access("comment_show", context, data_dict)

    id = tk.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(id)
    if not comment:
        raise tk.ObjectNotFound(tk._('Comment not found'))

    return comment.as_dict()


@tk.side_effect_free
def comment_count(context, data_dict):
    '''Return the number of active comments on a thread

    :param url: the URL of the commented object, e.g. ``/dataset/<name>``
    :param id: alternatively, the id of the thread
    '''
    tk.check_access('comment_count', context, data_dict)

    url = data_dict.get('url')
    id = data_dict.get('id')
    if url:
        return comment_model.CommentThread.count_from_url(url)
    if id:
        return comment_model.CommentThread.count(id)

    raise tk.ValidationError({'url': [tk._('Missing value')]})
