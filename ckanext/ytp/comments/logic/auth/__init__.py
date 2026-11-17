from ckanext.ytp.comments.logic.auth import create, delete, get, update


def get_auth_functions():
    return {
        'comment_create': create.comment_create,
        'comment_update': update.comment_update,
        'comment_show': get.comment_show,
        'comment_delete': delete.comment_delete,
        'comment_count': get.comment_count,
        'thread_show': get.thread_show,
    }
