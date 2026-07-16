from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.errors import DatabaseError
from src.services.seed_service import EXPECTED_DEMO_COUNTS, EXPECTED_EMPTY_COUNTS
from src.services.workspace_service import read_workspace_counts


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


def test_demo_button_initializes_temporary_database_and_session_metadata(tmp_path):
    database_path = tmp_path / "ui-demo.db"
    at = AppTest.from_file("app.py")
    at.session_state["database_path"] = str(database_path)
    at.run()
    at.button(key="btn_load_demo").click().run()

    assert not at.exception
    assert at.session_state["workspace_initialized"] is True
    assert at.session_state["workspace_mode"] == "DEMO"
    assert at.session_state["workspace_metadata"]["cooperative_name"] == (
        "Koperasi Tani Merapi Sejahtera"
    )
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS
    assert any("initialized successfully" in message.value for message in at.success)
    assert {metric.value for metric in at.metric} >= {"30", "42", "8", "16", "7"}


def test_empty_button_initializes_profile_only_temporary_database(tmp_path):
    database_path = tmp_path / "ui-empty.db"
    at = AppTest.from_file("app.py")
    at.session_state["database_path"] = str(database_path)
    at.run()
    at.button(key="btn_start_empty").click().run()

    assert not at.exception
    assert at.session_state["workspace_mode"] == "EMPTY"
    assert read_workspace_counts(database_path) == EXPECTED_EMPTY_COUNTS
    assert any("Empty workspace initialized" in message.value for message in at.success)
    assert {metric.value for metric in at.metric} == {"0"}


def test_english_demo_initialization_and_confirmed_reset_are_bilingual(tmp_path):
    database_path = tmp_path / "ui-reset.db"
    at = AppTest.from_file("app.py")
    at.session_state["database_path"] = str(database_path)
    at.run()
    at.radio[0].set_value("en").run()
    at.button(key="btn_load_demo").click().run()

    assert any("Data demo berhasil" in message.value for message in at.success)
    assert at.button(key="btn_reset_workspace").disabled is True
    at.checkbox(key="confirm_workspace_reset").check().run()
    assert at.button(key="btn_reset_workspace").disabled is False
    at.button(key="btn_reset_workspace").click().run()
    assert not at.exception
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS


def test_workspace_service_error_becomes_safe_bilingual_ui_message(tmp_path, monkeypatch):
    def fail_initialization(*args, **kwargs):
        raise DatabaseError("technical database detail")

    monkeypatch.setattr("src.services.workspace_service.initialize_workspace", fail_initialization)
    at = AppTest.from_file("app.py")
    at.session_state["database_path"] = str(tmp_path / "failed.db")
    at.run()
    at.button(key="btn_load_demo").click().run()

    assert not at.exception
    assert any("Database tidak dapat diakses" in message.value for message in at.error)
    assert all("technical database detail" not in message.value for message in at.error)
