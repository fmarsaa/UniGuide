"""Downloading the model on a new server, and reading the Firebase key from an environment
variable when the host cannot hold a key file. No network and no real Firebase is used."""

import hashlib
import json

import firebase_setup
import model_store


class _Response:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield self._payload


def _serve(monkeypatch, payload: bytes):
    monkeypatch.setattr(model_store.requests, "get", lambda *a, **k: _Response(payload))


def test_an_existing_model_file_is_left_alone(tmp_path):
    path = tmp_path / "model.pkl"
    path.write_bytes(b"already here")
    assert model_store.ensure_model(str(path), "http://example.invalid/m", "0" * 64) is True
    assert path.read_bytes() == b"already here"


def test_a_model_whose_checksum_matches_is_kept(tmp_path, monkeypatch):
    payload = b"model bytes"
    _serve(monkeypatch, payload)
    path = tmp_path / "model.pkl"
    assert model_store.ensure_model(str(path), "http://example.invalid/m", hashlib.sha256(payload).hexdigest()) is True
    assert path.read_bytes() == payload


def test_a_model_whose_checksum_differs_is_discarded(tmp_path, monkeypatch):
    _serve(monkeypatch, b"tampered")
    path = tmp_path / "model.pkl"
    assert model_store.ensure_model(str(path), "http://example.invalid/m", "0" * 64) is False
    assert not path.exists() and not (tmp_path / "model.pkl.part").exists()


def test_a_download_without_a_checksum_is_refused(tmp_path, monkeypatch):
    _serve(monkeypatch, b"anything")
    assert model_store.ensure_model(str(tmp_path / "model.pkl"), "http://example.invalid/m", None) is False


def test_no_url_and_no_file_means_no_model(tmp_path):
    assert model_store.ensure_model(str(tmp_path / "model.pkl"), None, None) is False


def test_the_firebase_key_can_come_from_an_environment_variable(monkeypatch):
    key = {"type": "service_account", "project_id": "demo"}
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT_JSON", json.dumps(key))
    assert firebase_setup.credential_source() == key


def test_a_key_file_path_is_used_when_there_is_no_variable(monkeypatch, tmp_path):
    key_file = tmp_path / "key.json"
    key_file.write_text("{}")
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT_PATH", str(key_file))
    assert firebase_setup.credential_source() == str(key_file)


def test_without_any_key_there_is_no_credential(monkeypatch):
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_PATH", raising=False)
    assert firebase_setup.credential_source() is None


def test_a_broken_variable_is_ignored_rather_than_crashing(monkeypatch):
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT_JSON", "{not json")
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_PATH", raising=False)
    assert firebase_setup.credential_source() is None
