from webhelpers.html import HTML, literal, tags, tools
from ckan import model
from ckan.lib.helpers import *


def linked_user_comments(user, maxlength=0, avatar=20):

    if not isinstance(user, model.User):
        user_name = unicode(user)
        user = model.User.get(user_name)
        if not user:
            return user_name
    if user:
        name = user.name if model.User.VALID_NAME.match(user.name) else user.id
        displayname = user.display_name
        user_name = user.name if model.User.VALID_NAME.match(user.name) else user.id

        if maxlength and len(user.display_name) > maxlength:
            displayname = displayname[:maxlength] + '...'

        if maxlength and len(user.name) > maxlength:
            user_name = user_name[:maxlength] + '...'

        return tags.literal(u'{icon} {link}'.format(
            icon=gravatar(
                email_hash=user.email_hash,
                size=avatar
            ),
            link=tags.link_to(
                user_name,
                url_for(controller='user', action='read', id=name)
            )
        ))