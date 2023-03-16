import datetime
import ckanext.ytp.comments.model as comment_model
import ckanext.ytp.comments.util as util
from ckan.plugins import toolkit
import logging

log = logging.getLogger(__name__)


def comment_update(context, data_dict):
    model = context['model']

    toolkit.check_access("comment_update", context, data_dict)

    cid = toolkit.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(cid)
    if not comment:
        toolkit.abort(404)

    # Validate that we have the required fields.
    if not all([data_dict.get('comment')]):
        raise toolkit.ValidationError("Comment text is required")

    # Cleanup the comment
    cleaned_comment = util.clean_input(data_dict.get('comment'))

    comment.subject = data_dict.get('subject')
    comment.comment = cleaned_comment
    comment.modified_date = datetime.datetime.now()

    model.Session.add(comment)
    model.Session.commit()

    return comment.as_dict()
