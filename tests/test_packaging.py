"""The offline Windows package: the launcher's decisions, without starting anything."""
import importlib.util
import socket
import subprocess
from pathlib import Path

import pytest

PACKAGING = Path(__file__).resolve().parents[1] / "packaging" / "windows"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"packaging_{name}", PACKAGING / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launch = _load("launch")
download_model = _load("download_model")
build = _load("build")


def test_settings_reads_only_known_names_and_skips_comments(tmp_path):
    path = tmp_path / "settings.txt"
    path.write_text("# a comment\n\nOPENAI_API_KEY = made-up-key \n# ANTHROPIC_API_KEY=commented-out\n"
                    "MESKA_LLM_BASE_URL=\"https://example.test/v1\"\nPATH=C:\\somewhere\nPYTHONPATH=evil\n"
                    "MESKA_LLM_MODEL=\nnot a setting line\n", encoding="utf-8")
    assert launch.read_settings(path) == {"OPENAI_API_KEY": "made-up-key",
                                          "MESKA_LLM_BASE_URL": "https://example.test/v1"}


def test_settings_file_may_be_missing(tmp_path):
    assert launch.read_settings(tmp_path / "settings.txt") == {}


def test_the_shipped_settings_file_sets_nothing():
    """Every line in the template is a comment, so a fresh package uses no key and no outside address."""
    assert launch.read_settings(PACKAGING / "files" / "settings.txt") == {}


def test_find_model_takes_the_largest_and_ignores_vision_addons_and_partial_downloads(tmp_path):
    assert launch.find_model(tmp_path / "missing") is None
    assert launch.find_model(tmp_path) is None
    (tmp_path / "mmproj-big.gguf").write_bytes(b"x" * 500)
    (tmp_path / "small.gguf").write_bytes(b"x" * 10)
    (tmp_path / "model.gguf").write_bytes(b"x" * 100)
    (tmp_path / "model.gguf.part").write_bytes(b"x" * 900)
    (tmp_path / "notes.txt").write_text("x" * 999)
    assert launch.find_model(tmp_path).name == "model.gguf"


def test_free_port_moves_past_a_port_in_use():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen(1)
        port = taken.getsockname()[1]
        assert not launch.port_is_free(port)
        assert launch.free_port(port) > port


def test_first_start_copies_the_school_once_and_never_overwrites(tmp_path):
    seed = tmp_path / "app" / "data"
    (seed / "inbox").mkdir(parents=True)
    (seed / "meska.db").write_text("seed")
    (seed / "inbox" / "note.txt").write_text("a note")
    assert launch.first_run_data(tmp_path) is True
    assert (tmp_path / "data" / "inbox" / "note.txt").read_text() == "a note"
    (tmp_path / "data" / "meska.db").write_text("the teacher's own work")
    assert launch.first_run_data(tmp_path) is False
    assert (tmp_path / "data" / "meska.db").read_text() == "the teacher's own work"


def test_app_environment_uses_only_the_package_and_this_computer(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "C:\\someone\\elses\\code")
    monkeypatch.setenv("PYTHONHOME", "C:\\another\\python")
    env = launch.child_env(tmp_path, {}, 8780, "http://127.0.0.1:11812/v1")
    assert env["PYTHONPATH"] == str(tmp_path / "app" / "src")
    assert "PYTHONHOME" not in env
    assert env["MESKA_WEB_HOST"] == "127.0.0.1"
    assert env["MESKA_DB"] == str(tmp_path / "data" / "meska.db")
    assert env["MESKA_LLM_BASE_URL"] == "http://127.0.0.1:11812/v1"
    assert env["MESKA_LLM_MODEL"] == launch.MODEL_NAME
    # The borrowed document reader runs from the package's own Python, never from a download.
    assert env["MESKA_MARKITDOWN_CMD"] == str(tmp_path / "runtime" / "python" / "python.exe")
    assert env["MESKA_MARKITDOWN_ARGS"] == "-S -m _markitdown_runner"
    assert env["HF_HUB_OFFLINE"] == "1"


def test_an_address_in_settings_replaces_the_local_model(tmp_path):
    settings = {"MESKA_LLM_BASE_URL": "https://example.test/v1", "MESKA_LLM_MODEL": "some/model",
                "MESKA_LLM_API_KEY": "made-up-key", "MESKA_WEB_PORT": "9000"}
    env = launch.child_env(tmp_path, settings, 9000, None)
    assert env["MESKA_LLM_BASE_URL"] == "https://example.test/v1"
    assert env["MESKA_LLM_MODEL"] == "some/model"
    assert env["MESKA_LLM_REASONING"] == "default"   # hosted endpoints reject the local-only hint
    assert env["MESKA_WEB_PORT"] == "9000"


def test_the_package_has_its_own_ports_beside_an_installed_meska_brain():
    """The earlier package may still run on 8765 and 11811 on the same computer."""
    assert launch.APP_PORT == 8780
    assert launch.RUNNER_PORT == 11812
    for name in ("READ ME FIRST.txt", "settings.txt"):
        text = (PACKAGING / "files" / name).read_text(encoding="utf-8")
        assert "127.0.0.1:8780" in text
        assert "8765" not in text and "11811" not in text


def test_the_launcher_names_no_curriculum_pack(tmp_path, monkeypatch):
    monkeypatch.delenv("MESKA_PACK", raising=False)
    assert "MESKA_PACK" not in launch.child_env(tmp_path, {}, 8780, None)


def test_the_build_seeds_the_default_school_and_names_no_pack(tmp_path, monkeypatch):
    assert build.SEED_COMMAND[-1] == "seed"
    monkeypatch.setenv("MESKA_PACK", "some-old-pack")
    monkeypatch.delenv("MESKA_DEMO_PACK", raising=False)
    env = build.package_env(tmp_path)
    assert "MESKA_PACK" not in env and "MESKA_DEMO_PACK" not in env
    monkeypatch.setenv("MESKA_DEMO_PACK", "egypt-maths")
    assert build.package_env(tmp_path)["MESKA_DEMO_PACK"] == "egypt-maths"


def test_the_source_line_survives_a_repository_with_no_commit(tmp_path):
    assert build.source_state(tmp_path / "missing") == "not yet committed"
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    assert build.source_state(tmp_path) == "not yet committed"


def test_the_package_is_named_athar():
    assert build.NAME == "Athar"
    names = {p.name for p in (PACKAGING / "files").iterdir()}
    assert {"Start Athar.cmd", "Stop Athar.cmd"} <= names
    assert not any("Meska" in name for name in names)
    read_me = (PACKAGING / "files" / "READ ME FIRST.txt").read_text(encoding="utf-8")
    assert '"Start Athar"' in read_me and '"Stop Athar"' in read_me


def test_without_a_model_no_local_address_is_set(tmp_path, monkeypatch):
    monkeypatch.delenv("MESKA_LLM_BASE_URL", raising=False)
    env = launch.child_env(tmp_path, {}, 8780, None)
    assert "MESKA_LLM_BASE_URL" not in env


def test_the_model_runner_listens_on_this_computer_only_and_stays_offline(tmp_path):
    command = launch.runner_command(tmp_path, tmp_path / "m.gguf", 11812)
    assert command[command.index("--host") + 1] == "127.0.0.1"
    assert "--offline" in command and "--no-webui" in command
    assert command[command.index("--alias") + 1] == launch.MODEL_NAME


def test_stop_without_a_running_copy_is_quiet(tmp_path):
    said = []
    assert launch.stop_running(tmp_path, say=said.append) == 0
    assert "not running" in said[0]


def test_download_continues_a_partial_file(tmp_path, monkeypatch):
    whole = bytes(range(256)) * 40
    seen = {}

    class Reply:
        def __init__(self, data, status):
            self.data, self.status = data, status

        def read(self, n):
            block, self.data = self.data[:n], self.data[n:]
            return block

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout=0):
        seen["range"] = request.get_header("Range")
        start = int(seen["range"].split("=")[1].rstrip("-")) if seen["range"] else 0
        return Reply(whole[start:], 206 if seen["range"] else 200)

    monkeypatch.setattr(download_model.urllib.request, "urlopen", fake_urlopen)
    target = tmp_path / "model.gguf"
    (tmp_path / "model.gguf.part").write_bytes(whole[:1000])

    class Quiet:
        def write(self, _):
            pass

        def flush(self):
            pass

    download_model.download("https://example.test/model.gguf", target, len(whole), out=Quiet())
    assert seen["range"] == "bytes=1000-"
    assert target.read_bytes() == whole
    assert not (tmp_path / "model.gguf.part").exists()
    assert download_model.sha256_of(target) == __import__("hashlib").sha256(whole).hexdigest()


def test_the_download_and_the_build_agree_on_the_model():
    assert download_model.MODEL_SHA256 == build.MODEL_SHA256
    assert download_model.MODEL_URL.startswith("https://huggingface.co/")
    assert download_model.MODEL_URL.endswith(download_model.MODEL_FILE)


def test_everything_the_build_fetches_is_pinned():
    for file_name, checksum in build.LLAMA.values():
        assert build.LLAMA_BUILD in file_name and len(checksum) == 64
    assert "==" in build.MARKITDOWN_MCP


@pytest.mark.parametrize("name", ["Start Athar.cmd", "Stop Athar.cmd", "Download the model.cmd"])
def test_the_start_files_use_only_the_python_in_the_package(name):
    text = (PACKAGING / "files" / name).read_text(encoding="utf-8")
    assert '"runtime\\python\\python.exe" -E -s' in text
    assert "http" not in text.lower()


def test_the_package_documents_have_no_dashes_and_no_key():
    for name in ("READ ME FIRST.txt", "settings.txt"):
        text = (PACKAGING / "files" / name).read_text(encoding="utf-8")
        assert "\u2014" not in text and "\u2013" not in text
        assert "sk-" not in text


def test_the_launcher_picks_a_chat_model_from_a_local_server(tmp_path, monkeypatch):
    """With no model file, a model program already running on this computer is used as it is."""
    assert launch.pick_model(["text-embedding-nomic", "qwen/qwen3.8-27b", "qwen3.5-9b"]) == "qwen3.5-9b"
    assert launch.pick_model(["text-embedding-nomic", "llama-3", "qwen3.5-9b-uncensored-x", "qwen/qwen3.8-27b"]) == "qwen/qwen3.8-27b"
    assert launch.pick_model(["text-embedding-nomic", "llama-3"]) == "llama-3"
    assert launch.pick_model(["text-embedding-nomic"]) is None and launch.pick_model([]) is None
    assert all(url.startswith("http://127.0.0.1:") for _, url in launch.LOCAL_SERVERS)      # this computer only
    monkeypatch.setattr(launch, "LOCAL_SERVERS", (("Nothing", "http://127.0.0.1:9/v1"),))
    assert launch.find_local_server(timeout=0.3) is None
    env = launch.child_env(tmp_path, {}, 8780, "http://127.0.0.1:1234/v1", "llama-3")
    assert env["MESKA_LLM_MODEL"] == "llama-3" and env["MESKA_LLM_BASE_URL"] == "http://127.0.0.1:1234/v1"
