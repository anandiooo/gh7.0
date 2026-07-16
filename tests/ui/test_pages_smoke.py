from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_renders_welcome_without_exception():
    at = AppTest.from_file("app.py").run()
    assert not at.exception


def test_welcome_screen_elements():
    at = AppTest.from_file("app.py").run()

    # Product identity
    md_texts = [m.value for m in at.markdown]
    assert any("MimpiTani" in text for text in md_texts), "Product identity missing"

    # Demo and Empty actions present
    button_keys = [b.key for b in at.button]
    assert "btn_load_demo" in button_keys, "Demo action missing"
    assert "btn_start_empty" in button_keys, "Empty action missing"

    # Language control
    assert len(at.radio) == 1, "Language control missing"
    assert at.radio[0].value == "id", "Default language should be ID"

    # Disclaimer present
    captions = [c.value for c in at.caption]
    assert any("prototype" in text.lower() for text in captions), "Disclaimer missing"


def test_page_modules_load():
    pages_dir = Path("pages")
    page_files = [
        "1_surplus_radar.py",
        "2_harvest_plans.py",
        "3_buyers_and_capacity.py",
        "4_analysis_and_simulation.py",
    ]

    for page_name in page_files:
        page_path = pages_dir / page_name
        assert page_path.exists(), f"Page {page_name} missing"

        at = AppTest.from_file(str(page_path)).run()
        assert not at.exception, f"Uncaught exception loading {page_name}: {at.exception}"


def test_home_screen_and_banner():
    at = AppTest.from_file("app.py")
    at.session_state["workspace_initialized"] = True
    at.session_state["workspace_mode"] = "DEMO"
    at.run()
    assert not at.exception

    # Prototype banner should be present
    md_texts = [m.value for m in at.markdown]
    assert any("simulasi" in text.lower() for text in md_texts), "Prototype banner missing"
