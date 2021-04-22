import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from api.models import Document

subprocess_case = [
    (0, "done", "Command line output test"),
    (1, "error", "Command line error"),
    (2, "error", "Command line error bis"),
]


@pytest.fixture(params=subprocess_case)
def subprocess_check_output(mocker, request):
    import subprocess

    mock_check_output = mocker.Mock()

    code, status, output = request.param
    if code == 0:
        mock_check_output.return_value = output
        return mock_check_output, request.param
    else:
        error = subprocess.CalledProcessError(code, "", output=output)
        mock_check_output.side_effect = error
        return mock_check_output, request.param


@pytest.fixture
def document_model(tmp_path):
    def return_new_document():
        now = datetime.now()
        expire = now + timedelta(hours=1)
        pid = uuid.uuid4()
        filename = f"{pid}_{int(expire.timestamp())}"
        x_input = tmp_path / Path(f"i_{filename}.pdf")
        output = tmp_path / Path(f"o_{filename}.pdf")
        output_json = tmp_path / Path(f"o_{filename}.json")
        output_txt = tmp_path / Path(f"o_{filename}.txt")

        x_input.touch()
        output.touch()
        output_json.touch()
        output_txt.touch()

        document = Document(
            pid=pid,
            lang=["eng"],
            input=x_input,
            output=output,
            output_json=output_json,
            output_txt=output_txt,
            code=random.randint(0, 9),
            status="received",
            created=now.isoformat(),
            processing=now + timedelta(minutes=random.randint(0, 4)),
            result="Result cmd",
            expire=expire.isoformat(),
            finished=now + timedelta(minutes=random.randint(4, 9)),
        )
        return document

    return return_new_document
