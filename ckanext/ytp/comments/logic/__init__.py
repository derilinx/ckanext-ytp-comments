def get_comment(data_dict):
    from ckan.plugins import toolkit
    import ckanext.ytp.comments.model as model

    comment = data_dict.get('comment')
    if not comment:
        id = toolkit.get_or_bust(data_dict, 'id')
        comment = model.Comment.get(id)
    return comment
