from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.enums import WorkspaceMode
from src.errors import DatabaseError
from src.services.analysis_service import AnalysisService
from src.services.seed_service import EXPECTED_DEMO_COUNTS, EXPECTED_EMPTY_COUNTS
from src.services.workspace_service import read_workspace_counts, reset_workspace
from src.ui.components import material_icon


def test_user_facing_ui_source_contains_no_emoji():
    ui_paths = [
        Path("app.py"),
        *Path("pages").glob("*.py"),
        *Path("src/ui").glob("*.py"),
        *Path("src/i18n").glob("*.json"),
    ]
    emoji_ranges = (
        (0x2300, 0x23FF),
        (0x2600, 0x27BF),
        (0x1F000, 0x1FAFF),
        (0xFE00, 0xFE0F),
    )
    offenders = {
        str(path): sorted(
            {
                character
                for character in path.read_text(encoding="utf-8")
                if any(start <= ord(character) <= end for start, end in emoji_ranges)
            }
        )
        for path in ui_paths
    }

    assert not {path: chars for path, chars in offenders.items() if chars}


def test_custom_material_icons_use_streamlit_ligature_class():
    icon = material_icon("inventory_2")

    assert 'class="stIconMaterial mt-material-icon"' in icon
    assert ">inventory_2</span>" in icon


def test_app_renders_welcome_without_exception():
    at = AppTest.from_file("app.py").run()
    assert not at.exception


def test_welcome_screen_elements():
    at = AppTest.from_file("app.py").run()

    # Product identity
    md_texts = [m.value for m in at.markdown]
    assert any("tetani" in text for text in md_texts), "Product identity missing"

    # Demo and Empty actions present
    button_keys = [b.key for b in at.button]
    assert "btn_load_demo" in button_keys, "Demo action missing"
    assert "btn_start_empty" in button_keys, "Empty action missing"

    # Language control
    assert len(at.radio) == 1, "Language control missing"
    assert at.radio[0].value == "id", "Default language should be ID"

    # Disclaimer present
    assert any("prototype" in text.lower() for text in md_texts), "Disclaimer missing"


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
    captions = {caption.value for caption in at.caption}
    assert any("**42**" in caption for caption in captions)
    assert any("**8**" in caption for caption in captions)
    assert any("**16**" in caption for caption in captions)
    assert any("**7**" in caption for caption in captions)


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
    assert any("**0**" in caption.value for caption in at.caption)


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


def test_seeded_harvest_page_renders_table_forms_and_cancel_confirmation(
    tmp_path,
):
    database_path = tmp_path / "harvest-page.db"
    reset_workspace(WorkspaceMode.DEMO, database_path)
    at = AppTest.from_file("pages/2_harvest_plans.py", default_timeout=10)
    at.session_state["workspace_initialized"] = True
    at.session_state["database_path"] = str(database_path)
    at.run()

    assert not at.exception
    assert at.dataframe
    assert any(button.label == "Tambah Rencana Panen" for button in at.button)
    assert at.button(key="cancel_harvest_button").disabled is True


def test_empty_workspace_renders_setup_checklist_and_first_farmer_form(tmp_path):
    database_path = tmp_path / "empty-onboarding.db"
    reset_workspace(WorkspaceMode.EMPTY, database_path)

    radar = AppTest.from_file("pages/1_surplus_radar.py", default_timeout=10)
    radar.session_state["workspace_initialized"] = True
    radar.session_state["database_path"] = str(database_path)
    radar.run()

    assert not radar.exception
    assert {button.key for button in radar.button} >= {
        "setup_step_0",
        "setup_step_1",
        "setup_step_2",
        "setup_step_3",
    }

    harvest = AppTest.from_file("pages/2_harvest_plans.py", default_timeout=10)
    harvest.session_state["workspace_initialized"] = True
    harvest.session_state["database_path"] = str(database_path)
    harvest.run()

    assert not harvest.exception
    assert any(button.label == "Simpan Petani" for button in harvest.button)


def test_seeded_buyer_capacity_page_renders_crud_and_capacity_controls(tmp_path):
    database_path = tmp_path / "buyer-page.db"
    reset_workspace(WorkspaceMode.DEMO, database_path)
    at = AppTest.from_file("pages/3_buyers_and_capacity.py", default_timeout=10)
    at.session_state["workspace_initialized"] = True
    at.session_state["database_path"] = str(database_path)
    at.run()

    assert not at.exception
    assert len(at.tabs) == 3
    labels = {button.label for button in at.button}
    assert "Tambah Buyer" in labels
    assert "Tambah Permintaan" in labels
    assert "Simpan Kapasitas Tujuh Hari" in labels


def test_analysis_page_renders_persisted_result_and_scenario_controls(tmp_path):
    database_path = tmp_path / "analysis-page.db"
    reset_workspace(WorkspaceMode.DEMO, database_path)
    AnalysisService(database_path).run_base(date.today())
    at = AppTest.from_file("pages/4_analysis_and_simulation.py", default_timeout=10)
    at.session_state["workspace_initialized"] = True
    at.session_state["database_path"] = str(database_path)
    at.run()

    assert not at.exception
    labels = {button.label for button in at.button}
    assert "Jalankan Analisis & Susun Penyaluran" in labels
    assert "Bandingkan Hasil" in labels
    assert at.dataframe
