from ckan.plugins import toolkit as tk


@tk.auth_allow_anonymous_access
def thread_show(context, data_dict):
    return {'success': True}


@tk.auth_allow_anonymous_access
def comment_show(context, data_dict):
    return {'success': True}


@tk.auth_allow_anonymous_access
def comment_count(context, data_dict):
    return {'success': True}
