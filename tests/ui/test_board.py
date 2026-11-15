from playwright.sync_api import expect

from tests.ui.pages.issue_pages import IssuePage
from tests.ui.pages.sprint_pages import BoardPage


def test_drag_card_to_done_saves_the_status(logged_in_page, make_issue, project_key):
    issue_key = make_issue("Drag me")
    board = BoardPage(logged_in_page).open(key=project_key)
    expect(board.card_in_column(issue_key, "todo")).to_be_visible()

    board.drag(issue_key, "done")

    expect(board.toast).to_contain_text(f"{issue_key} moved to Done")
    expect(board.column_count("done")).to_have_text("1")
    expect(board.column_count("todo")).to_have_text("0")

    # Did it really save? Reload the board, then check the issue page too.
    logged_in_page.reload()
    expect(board.card_in_column(issue_key, "done")).to_be_visible()
    expect(IssuePage(logged_in_page).open(issue_key=issue_key).status).to_have_text("Done")


def test_board_filter(logged_in_page, make_issue, project_key):
    login = make_issue("Fix login")
    docs = make_issue("Write docs")
    board = BoardPage(logged_in_page).open(key=project_key)

    board.filter("login")

    expect(board.card(login)).to_be_visible()
    expect(board.card(docs)).to_have_count(0)
