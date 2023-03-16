import ckan.plugins as plugins
from ckan.plugins import implements, toolkit
from . import helpers

import logging

log = logging.getLogger(__name__)


class YtpCommentsPlugin(plugins.SingletonPlugin):
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.IConfigurable)
    implements(plugins.IPackageController, inherit=True)
    implements(plugins.ITemplateHelpers, inherit=True)
    implements(plugins.IActions, inherit=True)
    implements(plugins.IAuthFunctions, inherit=True)
    implements(plugins.IBlueprint)

    # IConfigurer

    def configure(self, config):
        log.debug("Configuring comments module")
        from .model import init_tables
        init_tables()

    def update_config(self, config):
        toolkit.add_template_directory(config, "templates")
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/', 'comments')

    def get_helpers(self):
        return {
            'get_comment_thread': self._get_comment_thread,
            'get_comment_count_for_dataset': self._get_comment_count_for_dataset,
            'linked_user_comments': helpers.linked_user_comments,
            'get_site_captcha': helpers.get_site_captcha
        }

    def get_actions(self):
        from ckanext.ytp.comments.logic.action import get, create, delete, update

        return {
            "comment_create": create.comment_create,
            "thread_show": get.thread_show,
            "comment_update": update.comment_update,
            "comment_show": get.comment_show,
            "comment_delete": delete.comment_delete,
            "comment_count": get.comment_count
        }

    def get_auth_functions(self):
        from ckanext.ytp.comments.logic.auth import get, create, delete, update

        return {
            'comment_create': create.comment_create,
            'comment_update': update.comment_update,
            'comment_show': get.comment_show,
            'comment_delete': delete.comment_delete,
            "comment_count": get.comment_count
        }
    # IPackageController

    def before_view(self, pkg_dict):
        # TODO: append comments from model to pkg_dict
        return pkg_dict

    def get_blueprint(self):
        from .blueprint import blueprint
        return blueprint

    def _get_comment_thread(self, dataset_name):
        import ckan.model as model
        from ckan.logic import get_action
        url = '/dataset/%s' % dataset_name
        return get_action('thread_show')({'model': model, 'with_deleted': False}, {'url': url})

    def _get_comment_count_for_dataset(self, dataset_name):
        import ckan.model as model
        from ckan.logic import get_action
        url = '/dataset/%s' % dataset_name
        count = get_action('comment_count')({'model': model}, {'url': url})
        return count
