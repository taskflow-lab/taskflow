def test_app_starts_in_testing_mode(app):
    assert app.config["TESTING"] is True


def test_login_page_loads(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Log in" in response.data


def test_logged_in_user_sees_projects(logged_in_client):
    response = logged_in_client.get("/projects/")
    assert response.status_code == 200


def test_fixtures_create_project_and_issue(issue):
    assert issue.key == "WEB-1"
