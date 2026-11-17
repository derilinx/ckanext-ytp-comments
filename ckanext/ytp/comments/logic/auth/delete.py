from ckanext.ytp.comments.logic.auth.utils import user_is_comment_author


def comment_delete(context, data_dict):
    # Sysadmins bypass this check
    return user_is_comment_author(context, data_dict)
