from ckan import model
from ckan.plugins import toolkit as tk

import ckanext.ytp.comments.model as comment_model


def user_is_comment_author(context, data_dict):
    userobj = model.User.get(context.get('user'))
    if not userobj:
        return {'success': False, 'msg': tk._('You must be logged in')}

    comment = comment_model.Comment.get(tk.get_or_bust(data_dict, 'id'))
    if not comment:
        return {'success': False, 'msg': tk._('Comment does not exist')}

    if comment.user_id != userobj.id:
        return {
            'success': False,
            'msg': tk._('User is not the author of the comment')
        }

    return {'success': True}
