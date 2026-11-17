import logging

import ckan.plugins as plugins
from ckan.plugins import toolkit

from ckanext.ytp.comments import helpers
from ckanext.ytp.comments.blueprint import blueprint
from ckanext.ytp.comments.logic.action import get_actions
from ckanext.ytp.comments.logic.auth import get_auth_functions

log = logging.getLogger(__name__)


class YtpCommentsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, "templates")
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/', 'comments')

    # IConfigDeclaration
    def declare_config_options(self, declaration, key):
        declaration.annotate("ckanext-ytp-comments")
        declaration.declare_bool(key.ckan.comments.moderation, True)
        declaration.declare_bool(
            key.ckan.comments.moderation.first_only, True)
        declaration.declare(
            key.ckan.comments.annon_user, "anonymous").set_description(
            "Name of the user that comments are posted as. If the user "
            "does not exist, the site user is used.")
        declaration.declare_list(
            key.ckan.comments.notify_emails, ["jodie@derilinx.com"]
        ).set_description(
            "Email addresses to notify when a new comment is posted")

    # ITemplateHelpers
    def get_helpers(self):
        return helpers.get_helpers()

    # IActions
    def get_actions(self):
        return get_actions()

    # IAuthFunctions
    def get_auth_functions(self):
        return get_auth_functions()

    # IBlueprint
    def get_blueprint(self):
        return blueprint
