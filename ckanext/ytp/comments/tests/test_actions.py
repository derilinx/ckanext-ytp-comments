from unittest import mock

import pytest

from ckan import model
from ckan.plugins import toolkit as tk
from ckan.tests import factories, helpers

from ckanext.ytp.comments.model import Comment


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "ytp_comments"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


def _url(dataset):
    return "/dataset/{}".format(dataset["name"])


def _create_comment(dataset, **kwargs):
    data = {"url": _url(dataset), "subject": "Subject", "comment": "Some text"}
    data.update(kwargs)
    return helpers.call_action(
        "comment_create", {"user": "", "ignore_auth": False}, **data)


@pytest.fixture
def mail_recipient():
    with mock.patch("ckan.plugins.toolkit.mail_recipient") as m:
        yield m


@pytest.mark.usefixtures("mail_recipient")
class TestCommentCreate:

    def test_create_anonymous(self):
        dataset = factories.Dataset()

        comment = _create_comment(dataset)

        assert comment["subject"] == "Subject"
        assert "Some text" in comment["content"]
        assert comment["state"] == "active"
        assert comment["comments"] == []

        thread = helpers.call_action("thread_show", url=_url(dataset))
        assert thread["url"] == _url(dataset)
        assert [c["id"] for c in thread["comments"]] == [comment["id"]]

    def test_posted_as_site_user_by_default(self):
        dataset = factories.Dataset()

        comment = _create_comment(dataset)

        site_user = helpers.call_action("get_site_user")
        assert comment["user_id"] == model.User.get(site_user["name"]).id

    def test_posted_as_annon_user(self, ckan_config, monkeypatch):
        user = factories.User()
        monkeypatch.setitem(
            ckan_config, "ckan.comments.annon_user", user["name"])
        dataset = factories.Dataset()

        comment = _create_comment(dataset)

        assert comment["user_id"] == user["id"]

    def test_create_with_thread_id(self):
        dataset = factories.Dataset()
        first = _create_comment(dataset)

        second = helpers.call_action(
            "comment_create", thread_id=first["thread_id"], comment="Second")

        assert second["thread_id"] == first["thread_id"]

    def test_reply(self):
        dataset = factories.Dataset()
        parent = _create_comment(dataset)

        reply = _create_comment(
            dataset, comment="A reply", parent_id=parent["id"])

        parent = helpers.call_action("comment_show", id=parent["id"])
        assert [c["id"] for c in parent["comments"]] == [reply["id"]]

        thread = helpers.call_action("thread_show", url=_url(dataset))
        # Only top level comments are returned in the thread
        assert len(thread["comments"]) == 1
        assert len(thread["comments"][0]["comments"]) == 1

    def test_input_is_cleaned(self):
        dataset = factories.Dataset()

        comment = _create_comment(
            dataset,
            comment='<script>alert(1)</script><b>Hi</b> http://data.gov.ie')

        assert "<script>" not in comment["content"]
        assert "<b>" not in comment["content"]
        assert 'href="http://data.gov.ie"' in comment["content"]
        assert 'rel="nofollow noopener noreferrer"' in comment["content"]

    def test_missing_comment(self):
        dataset = factories.Dataset()

        with pytest.raises(tk.ValidationError) as e:
            _create_comment(dataset, comment="")

        assert "comment" in e.value.error_dict

    def test_missing_thread(self):
        with pytest.raises(tk.ValidationError) as e:
            helpers.call_action("comment_create", comment="Some text")

        assert "thread_id" in e.value.error_dict

    def test_notifies_officials(self, mail_recipient, ckan_config,
                                monkeypatch):
        monkeypatch.setitem(
            ckan_config, "ckan.comments.notify_emails",
            ["a@example.com", "b@example.com"])
        dataset = factories.Dataset()

        _create_comment(dataset)

        assert mail_recipient.call_count == 2
        args = mail_recipient.call_args[0]
        assert args[1] == "b@example.com"
        assert "http://test.ckan.net" + _url(dataset) in args[3]

    def test_captcha_required_in_production(self, monkeypatch, app):
        monkeypatch.setenv("PRODUCTION", "true")
        dataset = factories.Dataset()

        with app.flask_app.test_request_context(
                method="POST", data={"comment": "Some text"}):
            with pytest.raises(tk.ValidationError) as e:
                _create_comment(dataset)

        assert "captcha" in e.value.error_dict


@pytest.mark.usefixtures("mail_recipient")
class TestCommentUpdateDelete:

    def test_update(self):
        dataset = factories.Dataset()
        comment = _create_comment(dataset)

        updated = helpers.call_action(
            "comment_update", id=comment["id"], subject="New subject",
            comment="New text")

        assert updated["subject"] == "New subject"
        assert "New text" in updated["content"]
        assert updated["modified_date"]

    def test_update_not_found(self):
        with pytest.raises(tk.ObjectNotFound):
            helpers.call_action(
                "comment_update", id="unknown", comment="New text")

    def test_delete(self):
        dataset = factories.Dataset()
        comment = _create_comment(dataset)

        helpers.call_action("comment_delete", id=comment["id"])

        assert Comment.get(comment["id"]).state == "deleted"
        thread = helpers.call_action("thread_show", url=_url(dataset))
        assert thread["comments"] == []

        thread = helpers.call_action(
            "thread_show", {"with_deleted": True}, url=_url(dataset))
        assert len(thread["comments"]) == 1

    def test_delete_not_found(self):
        with pytest.raises(tk.ObjectNotFound):
            helpers.call_action("comment_delete", id="unknown")


@pytest.mark.usefixtures("mail_recipient")
class TestCommentCount:

    def test_count(self):
        dataset = factories.Dataset()
        first = _create_comment(dataset)
        _create_comment(dataset, parent_id=first["id"])
        deleted = _create_comment(dataset)
        helpers.call_action("comment_delete", id=deleted["id"])

        assert helpers.call_action("comment_count", url=_url(dataset)) == 2

    def test_count_no_thread(self):
        assert helpers.call_action(
            "comment_count", url="/dataset/unknown") == 0

    def test_count_by_id_includes_deleted(self):
        dataset = factories.Dataset()
        first = _create_comment(dataset)
        helpers.call_action("comment_delete", id=first["id"])

        assert helpers.call_action(
            "comment_count", id=first["thread_id"]) == 1


class TestThreadShow:

    def test_creates_thread(self):
        thread = helpers.call_action("thread_show", url="/dataset/some-name")

        assert thread["url"] == "/dataset/some-name"
        assert thread["comments"] == []

    def test_not_found(self):
        with pytest.raises(tk.ObjectNotFound):
            helpers.call_action("thread_show", id="unknown")


@pytest.mark.usefixtures("mail_recipient")
class TestAuth:

    @pytest.mark.parametrize(
        "action", ["comment_create", "comment_show", "comment_count",
                   "thread_show"])
    def test_anonymous_allowed(self, action):
        assert helpers.call_auth(action, {"user": ""}, id="some-id")

    @pytest.mark.parametrize("action", ["comment_update", "comment_delete"])
    def test_anonymous_not_allowed(self, action):
        dataset = factories.Dataset()
        comment = _create_comment(dataset)

        with pytest.raises(tk.NotAuthorized):
            helpers.call_auth(action, {"user": ""}, id=comment["id"])

    @pytest.mark.parametrize("action", ["comment_update", "comment_delete"])
    def test_other_user_not_allowed(self, action):
        dataset = factories.Dataset()
        comment = _create_comment(dataset)
        user = factories.User()

        with pytest.raises(tk.NotAuthorized):
            helpers.call_auth(action, {"user": user["name"]}, id=comment["id"])

    @pytest.mark.parametrize("action", ["comment_update", "comment_delete"])
    def test_author_allowed(self, action, ckan_config, monkeypatch):
        user = factories.User()
        monkeypatch.setitem(
            ckan_config, "ckan.comments.annon_user", user["name"])
        dataset = factories.Dataset()
        comment = _create_comment(dataset)

        assert helpers.call_auth(
            action, {"user": user["name"]}, id=comment["id"])

    @pytest.mark.parametrize("action", ["comment_update", "comment_delete"])
    def test_sysadmin_allowed(self, action):
        dataset = factories.Dataset()
        comment = _create_comment(dataset)
        sysadmin = factories.Sysadmin()

        assert helpers.call_auth(
            action, {"user": sysadmin["name"]}, id=comment["id"])

    @pytest.mark.parametrize("action", ["comment_update", "comment_delete"])
    def test_actions_check_auth(self, action):
        dataset = factories.Dataset()
        comment = _create_comment(dataset)
        user = factories.User()

        with pytest.raises(tk.NotAuthorized):
            helpers.call_action(
                action, {"user": user["name"], "ignore_auth": False},
                id=comment["id"], comment="New text")
        assert model.Session.query(Comment).get(comment["id"]).state == \
            "active"
