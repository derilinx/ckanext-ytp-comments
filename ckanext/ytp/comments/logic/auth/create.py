from ckan.plugins import toolkit as tk


@tk.auth_allow_anonymous_access
def comment_create(context, data_dict):
    # Anyone can comment, comments are posted as the anonymous comments user
    return {'success': True}
