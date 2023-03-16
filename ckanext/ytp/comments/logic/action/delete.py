import logging
import ckanext.ytp.comments.model as comment_model
from ckan.plugins import toolkit

log = logging.getLogger(__name__)


def comment_delete(context, data_dict):
    model = context['model']

    toolkit.check_access("comment_delete", context, data_dict)

    # Comment should either be set state=='deleted' if no children,
    # otherwise content should be set to withdrawn text
    id = toolkit.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(id)
    if not comment:
        toolkit.abort(404)

    comment.state = 'deleted'

    model.Session.add(comment)
    model.Session.commit()

    return {'success': True}
