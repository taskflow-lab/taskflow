import pytest

from app.modules.billing.services import PlanLimitError
from app.modules.projects import services


# ---------- create_project ----------

def test_create_project_sets_owner_as_member(app, user):
    project = services.create_project(user, "Website", "WEB", "Marketing site")

    assert project.key == "WEB"
    assert project.owner_id == user.id
    assert user in project.members
    assert project.is_archived is False


def test_create_project_uppercases_key(app, user):
    project = services.create_project(user, "Website", " web ")
    assert project.key == "WEB"


@pytest.mark.parametrize(
    "name, key, message",
    [
        ("", "WEB", "name is required"),
        ("N" * 121, "WEB", "120 characters"),
        ("Website", "W", "2-10 characters"),
        ("Website", "1WEB", "starting with a letter"),
        ("Website", "WEB-1", "letters and numbers"),
        ("Website", "ABCDEFGHIJK", "2-10 characters"),
    ],
)
def test_create_project_rejects_invalid_input(app, user, name, key, message):
    with pytest.raises(ValueError, match=message):
        services.create_project(user, name, key)


def test_create_project_rejects_duplicate_key(app, user, project):
    with pytest.raises(ValueError, match="already taken"):
        services.create_project(user, "Another", "web")


def test_create_project_respects_free_plan_limit(app, user, make_project):
    for _ in range(3):
        make_project()
    with pytest.raises(PlanLimitError):
        services.create_project(user, "Fourth", "FOUR")


def test_archived_projects_do_not_count_towards_limit(app, user, make_project):
    projects = [make_project() for _ in range(3)]
    services.archive_project(projects[0], user)

    services.create_project(user, "Fourth", "FOUR")  # allowed again


# ---------- lookup & listing ----------

def test_get_project_by_key_is_case_insensitive(app, project):
    assert services.get_project_by_key("web") == project


def test_get_project_by_key_missing(app):
    with pytest.raises(LookupError, match="not found"):
        services.get_project_by_key("NOPE")


def test_list_projects_includes_owned_and_member_projects(app, user, other_user, make_project):
    own = make_project(name="Mine", key="MINE")
    shared = make_project(owner=other_user, name="Shared", key="SHR", members=[user])
    make_project(owner=other_user, name="Private", key="PRV")

    assert services.list_projects_for_user(user) == [own, shared]


def test_list_projects_hides_archived_by_default(app, user, project):
    services.archive_project(project, user)

    assert services.list_projects_for_user(user) == []
    assert services.list_projects_for_user(user, include_archived=True) == [project]


# ---------- permissions ----------

def test_access_rules(app, user, other_user, admin_user, project):
    assert services.user_can_access(user, project) is True
    assert services.user_can_access(other_user, project) is False
    assert services.user_can_access(admin_user, project) is True
    assert services.user_can_access(None, project) is False


def test_member_can_access_but_not_manage(app, user, other_user, project):
    services.add_member(project, user, other_user.email)

    assert services.user_can_access(other_user, project) is True
    assert services.user_can_manage(other_user, project) is False


def test_only_owner_can_archive(app, user, other_user, project):
    services.add_member(project, user, other_user.email)
    with pytest.raises(PermissionError):
        services.archive_project(project, other_user)


# ---------- members ----------

def test_add_member(app, user, other_user, project):
    added = services.add_member(project, user, " BOB@test.com ")
    assert added == other_user
    assert other_user in project.members


def test_add_member_unknown_email(app, user, project):
    with pytest.raises(LookupError, match="No user"):
        services.add_member(project, user, "ghost@test.com")


def test_add_member_twice(app, user, other_user, project):
    services.add_member(project, user, other_user.email)
    with pytest.raises(ValueError, match="already a member"):
        services.add_member(project, user, other_user.email)


def test_owner_cannot_be_removed(app, user, project):
    with pytest.raises(ValueError, match="owner cannot be removed"):
        services.remove_member(project, user, user.id)


def test_remove_member(app, user, other_user, project):
    services.add_member(project, user, other_user.email)
    services.remove_member(project, user, other_user.id)
    assert other_user not in project.members


# ---------- update ----------

def test_update_project(app, project):
    services.update_project(project, name="  New name ", description=" Updated ")
    assert project.name == "New name"
    assert project.description == "Updated"


def test_update_project_rejects_empty_name(app, project):
    with pytest.raises(ValueError, match="name is required"):
        services.update_project(project, name="   ")
