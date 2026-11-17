import datetime

from ckan import model
from ckan.plugins import toolkit as tk

import ckanext.ytp.comments.model as comment_model
import ckanext.ytp.comments.util as util


def comment_update(context, data_dict):
    '''Update a comment

    :param id: the id of the comment
    :param comment: the comment text
    :param subject: the subject of the comment (optional)
    '''
    tk.check_access("comment_update", context, data_dict)

    cid = tk.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(cid)
    if not comment:
        raise tk.ObjectNotFound(tk._('Comment not found'))

    # Validate that we have the required fields.
    if not data_dict.get('comment'):
        raise tk.ValidationError({'comment': [tk._('Missing value')]})

    # Cleanup the comment
    cleaned_comment = util.clean_input(data_dict.get('comment'))

    comment.subject = data_dict.get('subject')
    comment.comment = cleaned_comment
    comment.modified_date = datetime.datetime.now()

    model.Session.add(comment)
    model.Session.commit()

    return comment.as_dict()
