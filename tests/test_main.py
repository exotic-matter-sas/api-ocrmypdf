import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time

import api.main
from api.main import app
from api.models import Document


@pytest.fixture(scope="class")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def document_upload():
    post_files_param = {"file": open("tests/test.pdf", "rb")}
    return post_files_param


class TestMain:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 204

    def test_status(self, monkeypatch, client):
        import subprocess

        def mock_check_output(*args, **kwargs):
            return "1.0.0"

        monkeypatch.setattr(subprocess, "check_output", mock_check_output)

        response = client.get("/status")
        assert response.status_code == 200
        json = response.json()
        assert {"status", "version_ocr"} <= json.keys()
        assert json == {"status": "ok", "version_ocr": mock_check_output()}

    @pytest.mark.parametrize(
        "test_input,expected", [("changeme", 200), ("invalid", 403)]
    )
    def test_basic_auth_header(
        self, monkeypatch, client, document_model, test_input, expected
    ):
        document = document_model()
        monkeypatch.setitem(api.main.documents, document.pid, document)

        response = client.get(f"/ocr/{document.pid}", headers={"X-API-KEY": test_input})
        assert response.status_code == expected

    def test_get_doc_detail(self, monkeypatch, document_model, client):
        document = document_model()
        monkeypatch.setitem(api.main.documents, document.pid, document)

        response = client.get(f"/ocr/{document.pid}", headers={"X-API-KEY": "changeme"})

        assert response.status_code == 200
        json = response.json()
        assert Document.parse_obj(json) == document

    def test_get_doc_pdf(self, monkeypatch, document_model, client):
        document = document_model()
        monkeypatch.setitem(api.main.documents, document.pid, document)

        response = client.get(
            f"/ocr/{document.pid}/pdf", headers={"X-API-KEY": "changeme"}
        )

        assert response.status_code == 200
        assert "Content-Type" in response.headers
        assert response.headers.get("Content-Type", None) == "application/pdf"

    def test_get_doc_txt(self, monkeypatch, document_model, client):
        document = document_model()
        monkeypatch.setitem(api.main.documents, document.pid, document)

        response = client.get(
            f"/ocr/{document.pid}/txt", headers={"X-API-KEY": "changeme"}
        )

        assert response.status_code == 200
        assert "Content-Type" in response.headers
        assert response.headers.get("Content-Type", None) == "text/plain; charset=utf-8"

    @freeze_time("2021-04-01 12:30:00")
    def test_ocr(self, monkeypatch, mocker, client, document_upload):
        from starlette.background import BackgroundTasks
        from api.models import Document
        from datetime import datetime, timedelta
        import uuid
        from pathlib import Path

        # Mocks
        mock_add_task = mocker.patch.object(BackgroundTasks, "add_task")
        mock_save_upload_file = mocker.patch.object(api.main, "save_upload_file")
        spy_uuid4 = mocker.spy(uuid, "uuid4")

        # Act
        response = client.post(
            "/ocr", files=document_upload, headers={"X-API-KEY": "changeme"}
        )

        # Assert
        assert response.status_code == 202

        mock_save_upload_file.assert_called_once()
        spy_uuid4.assert_called_once()

        args, _ = mock_save_upload_file.call_args
        x_now = datetime(year=2021, month=4, day=1, hour=12, minute=30)
        x_expire = x_now + timedelta(hours=1)
        x_filename = f"{spy_uuid4.spy_return}_{int(x_expire.timestamp())}"
        x_input = "workdir" / Path(f"i_{x_filename}.pdf")
        x_output_file = "workdir" / Path(f"o_{x_filename}.pdf")
        x_output_file_json = "workdir" / Path(f"o_{x_filename}.json")
        x_output_file_txt = "workdir" / Path(f"o_{x_filename}.txt")
        assert args[1] == x_input

        mock_add_task.assert_called_once()
        args, _ = mock_add_task.call_args
        assert args[0] == api.main.do_ocr
        assert isinstance(args[1], Document)

        json = response.json()
        assert json == {
            "pid": str(spy_uuid4.spy_return),
            "lang": ["eng"],
            "input": x_input.__str__(),
            "output": x_output_file.__str__(),
            "output_json": x_output_file_json.__str__(),
            "output_txt": x_output_file_txt.__str__(),
            "code": None,
            "status": "received",
            "created": x_now.isoformat(),
            "processing": None,
            "result": None,
            "expire": x_expire.isoformat(),
            "finished": None,
        }
