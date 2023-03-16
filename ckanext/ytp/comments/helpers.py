from ckan import model
from ckan.plugins import toolkit


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

        return toolkit.h.literal(u'{icon} {link}'.format(
            icon=toolkit.h.gravatar(
                email_hash=user.email_hash,
                size=avatar
            ),
            link=toolkit.h.tags.link_to(
                user_name,
                url_for(controller='user', action='read', id=name)
            )
        ))
    
    
def get_site_captcha():
    return '6LcKQEsUAAAAAExrtWZWOKD_dfYSCMSbpXpmbTXF'