from ckan import model
from ckan.plugins import toolkit as tk

import ckanext.ytp.comments.model as comment_model


def comment_delete(context, data_dict):
    '''Delete a comment (sets its state to "deleted")

    :param id: the id of the comment
    '''
    tk.check_access("comment_delete", context, data_dict)

    cid = tk.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(cid)
    if not comment:
        raise tk.ObjectNotFound(tk._('Comment not found'))

    comment.state = 'deleted'

    model.Session.add(comment)
    model.Session.commit()

    return {'success': True}
