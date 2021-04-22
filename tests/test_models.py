from api.models import Document


class TestDocumentModel:
    def test_delete_all_files(self, document_model):
        document = document_model()

        assert document.input.exists()
        assert document.output.exists()
        assert document.output_txt.exists()
        assert document.output_json.exists()

        document.delete_all_files()

        assert not document.input.exists()
        assert not document.output.exists()
        assert not document.output_txt.exists()
        assert not document.output_json.exists()

    def test_save_state(self, document_model):
        document = document_model()

        document.save_state()

        parsed_doc = Document.parse_file(document.output_json)
        assert parsed_doc == document

    def test_ocr(self, monkeypatch, tmp_path, document_model, subprocess_check_output):
        import subprocess
        import api.settings

        # Change current basedir so we can compute relative path later correctly
        monkeypatch.setattr(api.settings.config, "basedir", tmp_path)
        output, param = subprocess_check_output
        monkeypatch.setattr(subprocess, "check_output", output)

        document = document_model()

        document.ocr()

        assert document.code == param[0]
        assert document.status == param[1]
        assert document.result == param[2]
        assert document.finished > document.created
        output.assert_called_once_with(
            " ".join(
                [
                    api.settings.config.base_command_ocr,
                    api.settings.config.base_command_option,
                    f"-l {'+'.join([l.value for l in document.lang])}",
                    f"--sidecar {document.output_txt.resolve().relative_to(api.settings.config.basedir).as_posix()}",
                    document.input.resolve()
                    .relative_to(api.settings.config.basedir)
                    .as_posix(),
                    document.output.resolve()
                    .relative_to(api.settings.config.basedir)
                    .as_posix(),
                ]
            ),
            stderr=subprocess.STDOUT,
            shell=True,
        )
