import datetime
import logging
import uuid
from typing import List, Optional
from urllib.parse import urlparse

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, backref, relationship

from ckan import model
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)

COMMENT_APPROVED = "approved"
COMMENT_PENDING = "pending"


def make_uuid():
    return str(uuid.uuid4())


class CommentThread(tk.BaseModel):
    """
    Represents a thread, or in this particular case a collection of
    comments against a CKAN object, identified by its URL path.
    """
    __table__ = sa.Table(
        "comment_thread",
        tk.BaseModel.metadata,
        sa.Column("id", sa.UnicodeText, primary_key=True, default=make_uuid),
        sa.Column("url", sa.UnicodeText),
        sa.Column(
            "creation_date", sa.DateTime, default=datetime.datetime.now),
        sa.Column("locked", sa.Boolean, default=False),
    )

    id: Mapped[str]
    url: Mapped[Optional[str]]
    creation_date: Mapped[Optional[datetime.datetime]]
    locked: Mapped[Optional[bool]]

    @classmethod
    def clean_url(cls, incoming):
        """
        We are only interested in the path, so we will strip out
        everything else
        """
        return urlparse(incoming).path

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_by_url(cls, threadurl):
        return model.Session.query(cls).filter(
            cls.url == cls.clean_url(threadurl)).first()

    @classmethod
    def from_url(cls, threadurl):
        """
        Returns the thread for that URL, creating it if it does not exist
        """
        thread = cls.get_by_url(threadurl)
        if not thread:
            thread = cls(url=cls.clean_url(threadurl))
            model.Session.add(thread)
            model.Session.commit()

        return thread

    @classmethod
    def count_from_url(cls, threadurl):
        """
        Number of active comments (including replies) on the thread for
        that URL, or 0 if there is no thread
        """
        thread = cls.get_by_url(threadurl)
        if not thread:
            return 0
        return cls._count_comments(thread.id, only_active=True)

    @classmethod
    def count(cls, id):
        """
        Number of comments (including replies and deleted comments) on the
        thread with that id, or 0 if there is no thread
        """
        thread = cls.get(id)
        if not thread:
            return 0
        return cls._count_comments(thread.id, only_active=False)

    @classmethod
    def _count_comments(cls, thread_id, only_active):
        children = model.Session.query(
            Comment.id,
            Comment.parent_id,
            Comment.thread_id)
        if only_active:
            children = children.filter(Comment.state == 'active')
        children = children.cte(name='children', recursive=True)

        children = children.union_all(
            model.Session.query(
                Comment.id,
                Comment.parent_id,
                Comment.thread_id
            )
            .filter(Comment.id == children.c.parent_id)
        )

        q = model.Session.query(
            sa.func.count('*').label('comment_count'),
            children.c.thread_id
        ).group_by(children.c.thread_id).filter(
            children.c.parent_id == None  # noqa: E711
        ).subquery()

        count = model.Session.query(
            sa.func.sum(q.c.comment_count)
        ).group_by(q.c.thread_id).filter(q.c.thread_id == thread_id).scalar()

        return int(count) if count else 0

    def as_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'locked': self.locked,
            'created': self.creation_date.isoformat(),
        }


class Comment(tk.BaseModel):
    """
    A comment is a text block provided by a user against an object, or in this
    particular case a CommentThread (one per object).
    """
    __table__ = sa.Table(
        "comment",
        tk.BaseModel.metadata,
        sa.Column("id", sa.UnicodeText, primary_key=True, default=make_uuid),
        sa.Column("parent_id", sa.UnicodeText, sa.ForeignKey("comment.id")),
        sa.Column(
            "thread_id", sa.UnicodeText, sa.ForeignKey("comment_thread.id"),
            nullable=True),
        sa.Column(
            "user_id", sa.UnicodeText, sa.ForeignKey(model.User.id),
            nullable=False),
        sa.Column("subject", sa.UnicodeText),
        sa.Column("comment", sa.UnicodeText),
        sa.Column(
            "creation_date", sa.DateTime, default=datetime.datetime.now),
        sa.Column("modified_date", sa.DateTime),
        sa.Column("approval_status", sa.UnicodeText),
        sa.Column("state", sa.UnicodeText, default=u'active'),
    )

    id: Mapped[str]
    parent_id: Mapped[Optional[str]]
    thread_id: Mapped[Optional[str]]
    user_id: Mapped[str]
    subject: Mapped[Optional[str]]
    comment: Mapped[Optional[str]]
    creation_date: Mapped[Optional[datetime.datetime]]
    modified_date: Mapped[Optional[datetime.datetime]]
    approval_status: Mapped[Optional[str]]
    state: Mapped[Optional[str]]

    children: Mapped[List["Comment"]] = relationship(
        "Comment",
        lazy="joined",
        join_depth=10,
        backref=backref('parent', remote_side=[__table__.c.id]),
        order_by="asc(Comment.creation_date)",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Auto-set some values based on configuration
        if tk.asbool(tk.config.get('ckan.comments.moderation', True)):
            self.approval_status = COMMENT_PENDING
        else:
            # If user wants first comment moderated and the user who wrote
            # this hasn't got another comment, put it into moderation,
            # otherwise approve
            if tk.asbool(tk.config.get(
                    'ckan.comments.moderation.first_only', True)) and \
                    Comment.count_for_user(
                        self.user_id, COMMENT_APPROVED) == 0:
                self.approval_status = COMMENT_PENDING
            else:
                self.approval_status = COMMENT_APPROVED

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def count_for_user(cls, user_id, status):
        return model.Session.query(cls) \
            .filter(cls.approval_status == status) \
            .filter(cls.user_id == user_id).count()

    def as_dict(self, only_active_children=True):
        """
        Returns this model as a dictionary, including all child comments (as
        dicts) if it has any
        """
        name = 'anonymous'
        u = model.User.get(self.user_id)
        if u:
            name = u.fullname

        # Hack
        if name == tk.config.get('ckan.site_id') or not name:
            name = 'anonymous'

        d = {
            'id': self.id,
            'user_id': self.user_id,
            'username': name,
            'subject': self.subject,
            'content': self.comment,
            'state': self.state,
            'thread_id': self.thread_id,
            'creation_date': self.creation_date.isoformat(),
        }
        if self.modified_date:
            d['modified_date'] = self.modified_date.isoformat()

        d['comments'] = [
            c.as_dict(only_active_children=only_active_children)
            for c in self.children
            if c.state == 'active' or not only_active_children
        ]
        return d


class CommentBlockedUser(tk.BaseModel):
    """
    A blocked user who is not allowed to post anymore because they have
    previously posted spam.
    """
    __table__ = sa.Table(
        "comment_blocked",
        tk.BaseModel.metadata,
        sa.Column("id", sa.UnicodeText, primary_key=True, default=make_uuid),
        sa.Column("user_id", sa.UnicodeText, sa.ForeignKey(model.User.id)),
        sa.Column(
            "blocked_by", sa.UnicodeText, sa.ForeignKey(model.User.id)),
        sa.Column(
            "creation_date", sa.DateTime, default=datetime.datetime.now),
    )

    id: Mapped[str]
    user_id: Mapped[Optional[str]]
    blocked_by: Mapped[Optional[str]]
    creation_date: Mapped[Optional[datetime.datetime]]
