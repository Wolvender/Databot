# test_app_smoke.py - Renders the app headlessly and checks for exceptions
"""
Smoke test using Streamlit's AppTest: executes databot_app_refactored.py
without a browser, once logged out (login page) and once logged in (main tabs).

Run with:  python test_app_smoke.py
"""

from streamlit.testing.v1 import AppTest


def test_login_page_renders():
    at = AppTest.from_file("databot_app_refactored.py", default_timeout=30)
    at.run()
    assert not at.exception, f"Login page raised: {at.exception}"
    # Login form should be present
    assert any("Username" in (ti.label or "") for ti in at.text_input), "No username field on login page"
    print("  login page ... OK")


def test_main_app_renders_when_logged_in():
    at = AppTest.from_file("databot_app_refactored.py", default_timeout=30)
    at.session_state["logged_in"] = True
    at.session_state["username"] = "admin"
    at.run()
    assert not at.exception, f"Main app raised: {at.exception}"
    # All three tabs should exist
    assert len(at.tabs) == 3, f"Expected 3 tabs, got {len(at.tabs)}"
    print("  main app (logged in) ... OK")


if __name__ == "__main__":
    print("Running app smoke tests...")
    test_login_page_renders()
    test_main_app_renders_when_logged_in()
    print("All smoke tests passed.")
