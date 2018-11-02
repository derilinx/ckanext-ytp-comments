import logging
from ckan.common import _
import ckan.plugins as p


log = logging.getLogger(__name__)


@p.toolkit.auth_allow_anonymous_access
def comment_create(context, data_dict):
    # user = context['user']
    # model = context['model']
    #
    # userobj = model.User.get(user)

    return {'success': True}
