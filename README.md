ckanext-ytp-comments
====================

CKAN extension for adding comments to datasets.

Anyone can comment on public datasets. Comments are posted as the user defined
in `ckan.comments.annon_user` (or the site user if that user does not exist).
Sysadmins can reply to, edit and delete comments.

Some of the code is taken from [ckanext-comments](https://github.com/rossjones/ckanext-comments)


## Compatibility

Tested with CKAN 2.11

## Installation

Install to your CKAN virtual environment:

```
pip install -e .
```

Add to ckan.ini:

```
ckan.plugins = ... ytp_comments
```

Create the database tables:

```
ckan db upgrade -p ytp_comments
```

Sites that already have the tables (created by older versions of the
extension) can run the same command: the migration detects the existing tables
and only records the migration as applied.

## Configuration

```
# Name of the user that comments are posted as (default: anonymous)
ckan.comments.annon_user = anonymous

# Email addresses to notify when a new comment is posted (space separated)
ckan.comments.notify_emails = someone@example.com

# Moderation flags, stored with each comment (default: true)
ckan.comments.moderation = false
ckan.comments.moderation.first_only = false
```

When the `PRODUCTION` environment variable is set to `true`, new comments
require a valid reCAPTCHA response (`ckan.captcha_secret`).

## Tests

```
pytest --ckan-ini=test.ini ckanext/ytp/comments/tests
```
