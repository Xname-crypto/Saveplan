import zipfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.conversions import (
    ConversionAssetPayload,
    MEDIA_DIR,
    OcrResult,
    TesseractOcrProvider,
    apply_asset_transcripts,
    bind_assets_to_detected_markers,
    extract_docx_text,
    extract_pdf_text,
)
from backend.app.kshuati_converter import ParsedQuestion


def test_docx_media_files_are_returned_as_pending_ocr_assets(tmp_path: Path):
    docx_path = tmp_path / "with-image.docx"
    document_xml = """
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>1.图片题题干</w:t></w:r></w:p>
        <w:p><w:r><w:t>A.选项一</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/image1.png", b"fake-image")

    text, issues, assets = extract_docx_text(docx_path)

    assert "1.图片题题干" in text
    assert any("DOCX 包含图片" in issue for issue in issues)
    assert assets[0]["kind"] == "image"
    assert assets[0]["status"] == "pending_ocr"
    assert assets[0]["filename"] == "image1.png"


def test_docx_media_files_are_ignored_when_assets_are_disabled(tmp_path: Path):
    docx_path = tmp_path / "without-assets.docx"
    document_xml = """
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>1.图片题题干</w:t></w:r></w:p>
        <w:p><w:r><w:t>A.选项一</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/image1.png", b"fake-image")

    text, issues, assets = extract_docx_text(docx_path, include_assets=False)

    assert "1.图片题题干" in text
    assert not any("DOCX 包含图片" in issue for issue in issues)
    assert assets == []


def test_docx_inline_images_insert_position_marker(tmp_path: Path):
    docx_path = tmp_path / "with-inline-image.docx"
    document_xml = """
    <w:document
      xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <w:body>
        <w:p>
          <w:r><w:t>1.观察</w:t></w:r>
          <w:r><w:drawing><a:blip r:embed="rId1" /></w:drawing></w:r>
          <w:r><w:t>，下列正确的是（ ）</w:t></w:r>
        </w:p>
        <w:p><w:r><w:t>A.甲</w:t></w:r></w:p>
        <w:p><w:r><w:t>B.乙</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    rels_xml = """
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png" />
    </Relationships>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", rels_xml)
        archive.writestr("word/media/image1.png", b"fake-image")

    text, issues, assets = extract_docx_text(docx_path)

    assert "1.观察[图片1]，下列正确的是（ ）" in text
    assert any("DOCX 包含图片" in issue for issue in issues)
    assert len(assets) == 1
    assert assets[0]["filename"] == "image1.png"
    assert assets[0]["marker"] == "[图片1]"
    assert "[图片1]" in assets[0]["note"]


def test_docx_formula_objects_are_marked_for_manual_review(tmp_path: Path):
    docx_path = tmp_path / "with-formula.docx"
    document_xml = """
    <w:document
      xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
      xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <w:body>
        <w:p>
          <w:r><w:t>1.函数</w:t></w:r>
          <m:oMathPara>
            <m:oMath>
              <m:r><m:t>y=x^2</m:t></m:r>
            </m:oMath>
          </m:oMathPara>
          <w:r><w:t>的图像是（ ）</w:t></w:r>
        </w:p>
        <w:p><w:r><w:t>A.直线</w:t></w:r></w:p>
        <w:p><w:r><w:t>B.抛物线</w:t></w:r></w:p>
        <w:p><w:r><w:t>C.双曲线</w:t></w:r></w:p>
        <w:p><w:r><w:t>D.圆</w:t></w:r></w:p>
        <w:p><w:r><w:t>答案:B</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    text, issues, assets = extract_docx_text(docx_path)

    assert "1.函数[公式1]的图像是（ ）" in text
    assert any("DOCX 包含公式对象" in issue for issue in issues)
    assert len(assets) == 1
    assert assets[0]["source"] == "docx_formula"
    assert assets[0]["status"] == "manual_review"
    assert assets[0]["marker"] == "[公式1]"
    assert assets[0]["transcript"] == "y=x^2"
    assert "公式1" in assets[0]["note"]


def test_docx_media_files_are_saved_when_conversion_id_is_provided(tmp_path: Path):
    docx_path = tmp_path / "with-image.docx"
    document_xml = """
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body><w:p><w:r><w:t>1.图片题</w:t></w:r></w:p></w:body>
    </w:document>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/image1.png", b"fake-image")

    _text, _issues, assets = extract_docx_text(docx_path, conversion_id="test-media")

    assert assets[0]["preview_url"] is None
    assert assets[0]["stored_path"]
    assert Path(str(assets[0]["stored_path"])).exists()
    assert MEDIA_DIR.name in Path(str(assets[0]["stored_path"])).parts


def test_pdf_page_images_are_returned_as_pending_ocr_assets(tmp_path: Path, monkeypatch):
    class FakeImage:
        name = "figure.png"
        data = b"pdf-image"

    class FakePage:
        images = [FakeImage()]

        def extract_text(self):
            return "1.含图题\nA.甲\nB.乙\nC.丙\nD.丁\n答案:A"

    class FakeReader:
        def __init__(self, _path):
            self.pages = [FakePage()]

    monkeypatch.setattr("backend.app.conversions.PdfReader", FakeReader)
    pdf_path = tmp_path / "with-image.pdf"
    pdf_path.write_bytes(b"%PDF fake")

    text, issues, assets = extract_pdf_text(pdf_path, conversion_id="pdf-media")

    assert "含图题" in text
    assert issues == []
    assert assets[0]["kind"] == "image"
    assert assets[0]["source"] == "pdf"
    assert assets[0]["page"] == 1
    assert Path(str(assets[0]["stored_path"])).exists()


def test_asset_transcript_can_be_bound_to_question_stem():
    question = ParsedQuestion(
        number=1,
        stem="观察下图，选择正确结论。",
        options={"A": "甲", "B": "乙", "C": "丙", "D": "丁"},
        answer="A",
    )
    asset = ConversionAssetPayload(
        id="asset-1",
        kind="image",
        source="docx",
        status="manual_review",
        note="图像题",
        filename="image1.png",
        transcript="图中抛物线开口向上，顶点在原点。",
        target_question_number=1,
        target_field="stem",
    )

    apply_asset_transcripts([question], [asset])

    assert "[image1.png] 图中抛物线开口向上，顶点在原点。" in question.stem


def test_asset_transcript_can_be_bound_to_question_option():
    question = ParsedQuestion(
        number=1,
        stem="选择含图选项。",
        options={"A": "文字选项", "B": "见图", "C": "普通选项", "D": "普通选项"},
        answer="B",
    )
    asset = ConversionAssetPayload(
        id="asset-option",
        kind="image",
        source="docx",
        status="manual_review",
        note="选项图片",
        filename="option-b.png",
        transcript="图中函数单调递增。",
        target_question_number=1,
        target_field="option_B",
    )

    apply_asset_transcripts([question], [asset])

    assert question.options["B"] == "见图\n[option-b.png] 图中函数单调递增。"


def test_asset_transcript_replaces_matching_marker_in_stem():
    question = ParsedQuestion(
        number=1,
        stem="观察[图片1]，选择正确结论。",
        options={"A": "甲", "B": "乙", "C": "丙", "D": "丁"},
        answer="A",
    )
    asset = ConversionAssetPayload(
        id="asset-marker",
        kind="image",
        source="docx",
        status="manual_review",
        note="题干图片",
        marker="[图片1]",
        filename="image1.png",
        transcript="图中细胞正在进行有丝分裂。",
        target_question_number=1,
        target_field="stem",
    )

    apply_asset_transcripts([question], [asset])

    assert question.stem == "观察[image1.png] 图中细胞正在进行有丝分裂。，选择正确结论。"


def test_assets_are_auto_bound_to_option_marker():
    question = ParsedQuestion(
        number=2,
        stem="选择正确图像。",
        options={"A": "文字选项", "B": "[图片1]", "C": "普通选项", "D": "普通选项"},
        answer="B",
    )
    assets = [
        {
            "id": "asset-option-marker",
            "kind": "image",
            "source": "docx",
            "status": "pending_ocr",
            "note": "选项图片",
            "marker": "[图片1]",
            "filename": "option-b.png",
            "transcript": "",
            "target_question_number": None,
            "target_field": "stem",
        }
    ]

    bound_assets = bind_assets_to_detected_markers(assets, [question])

    assert bound_assets[0]["target_question_number"] == 2
    assert bound_assets[0]["target_field"] == "option_B"


def test_asset_preview_endpoint_requires_owner_and_returns_file(tmp_path: Path):
    client = TestClient(app)
    email = "preview-test@example.com"
    password = "password123"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "username": "preview-test",
            "job": "student",
            "interests": [],
        },
    )
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
    token = response.json()["token"]

    docx_path = tmp_path / "preview.docx"
    document_xml = """
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>1.图片题</w:t></w:r></w:p>
        <w:p><w:r><w:t>A.甲</w:t></w:r></w:p>
        <w:p><w:r><w:t>B.乙</w:t></w:r></w:p>
        <w:p><w:r><w:t>C.丙</w:t></w:r></w:p>
        <w:p><w:r><w:t>D.丁</w:t></w:r></w:p>
        <w:p><w:r><w:t>答案:A</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/image1.png", b"fake-image")

    with docx_path.open("rb") as file:
        created = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    "preview.docx",
                    file,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    payload = created.json()
    preview_url = payload["assets"][0]["preview_url"]
    preview = client.get(preview_url, headers={"Authorization": f"Bearer {token}"})

    assert preview.status_code == 200
    assert preview.content == b"fake-image"


def register_and_login(client: TestClient) -> str:
    email = f"conversion-{uuid.uuid4().hex}@example.com"
    password = "password123"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "username": "conversion-test",
            "job": "student",
            "interests": [],
        },
    )
    assert response.status_code in {200, 201}
    return response.json()["token"]


def create_conversion_with_image_asset(client: TestClient, tmp_path: Path, token: str) -> dict:
    docx_path = tmp_path / f"ocr-{uuid.uuid4().hex}.docx"
    document_xml = """
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>1. Image question</w:t></w:r></w:p>
        <w:p><w:r><w:t>A. One</w:t></w:r></w:p>
        <w:p><w:r><w:t>B. Two</w:t></w:r></w:p>
        <w:p><w:r><w:t>C. Three</w:t></w:r></w:p>
        <w:p><w:r><w:t>D. Four</w:t></w:r></w:p>
        <w:p><w:r><w:t>Answer:A</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/image1.png", b"fake-image")

    with docx_path.open("rb") as file:
        response = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    docx_path.name,
                    file,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["assets"]
    return payload


def test_ocr_asset_endpoint_keeps_manual_review_when_tesseract_is_missing(tmp_path: Path, monkeypatch):
    client = TestClient(app)
    token = register_and_login(client)
    conversion = create_conversion_with_image_asset(client, tmp_path, token)
    asset = conversion["assets"][0]
    monkeypatch.setattr("backend.app.conversions.shutil.which", lambda _name: None)

    response = client.post(
        f"/api/conversions/{conversion['id']}/assets/{asset['id']}/ocr",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Tesseract" in payload["message"]
    assert payload["asset"]["status"] == "unsupported"
    assert payload["asset"]["transcript"] == ""


def test_ocr_asset_endpoint_saves_recognized_text(tmp_path: Path, monkeypatch):
    client = TestClient(app)
    token = register_and_login(client)
    conversion = create_conversion_with_image_asset(client, tmp_path, token)
    asset = conversion["assets"][0]

    class FakeOcrProvider:
        name = "fake"

        def recognize(self, _path, _subject):
            return OcrResult(
                transcript="recognized formula y=x^2",
                message="OCR done",
                provider=self.name,
            )

    monkeypatch.setattr("backend.app.conversions.get_ocr_provider", lambda _subject: FakeOcrProvider())

    response = client.post(
        f"/api/conversions/{conversion['id']}/assets/{asset['id']}/ocr",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "OCR done"
    assert payload["asset"]["status"] == "manual_review"
    assert payload["asset"]["transcript"] == "recognized formula y=x^2"


def test_tesseract_provider_prefers_english_first_for_formula_subjects(tmp_path: Path, monkeypatch):
    image_path = tmp_path / "formula.png"
    image_path.write_bytes(b"fake-image")
    commands = []

    monkeypatch.setattr("backend.app.conversions.shutil.which", lambda _name: "tesseract")

    def fake_run(command, capture_output, text, timeout, check):
        commands.append(command)
        output_base = Path(command[2])
        output_base.with_suffix(".txt").write_text("formula result", encoding="utf-8")

        class Completed:
            returncode = 0
            stderr = ""

        return Completed()

    monkeypatch.setattr("backend.app.conversions.subprocess.run", fake_run)

    result = TesseractOcrProvider().recognize(image_path, "math")

    assert result.transcript == "formula result"
    assert result.provider == "tesseract"
    assert commands[0][commands[0].index("-l") + 1] == "eng+chi_sim"


def test_conversion_api_upload_review_history_and_export(tmp_path: Path):
    client = TestClient(app)
    token = register_and_login(client)
    paper_path = tmp_path / "single-choice.txt"
    paper_path.write_text(
        """
1. 下列说法正确的是（ ）
A. 选项甲
B. 选项乙
C. 选项丙
D. 选项丁
答案: B
解析: 原解析
""".strip(),
        encoding="utf-8",
    )

    with paper_path.open("rb") as file:
        created = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            data={"subject": "politics"},
            files={"file": ("single-choice.txt", file, "text/plain")},
        )

    assert created.status_code == 201
    conversion = created.json()
    assert conversion["filename"] == "single-choice.txt"
    assert conversion["subject"] == "politics"
    assert conversion["question_count"] == 1
    assert conversion["questions"][0]["answer"] == "B"

    history = client.get("/api/conversions", headers={"Authorization": f"Bearer {token}"})
    assert history.status_code == 200
    assert any(item["id"] == conversion["id"] for item in history.json())

    detail = client.get(
        f"/api/conversions/{conversion['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == 200
    assert detail.json()["questions"][0]["options"]["C"] == "选项丙"

    reviewed_questions = detail.json()["questions"]
    reviewed_questions[0]["answer"] = "C"
    reviewed_questions[0]["analysis"] = "人工校对后的解析"
    reviewed = client.put(
        f"/api/conversions/{conversion['id']}/questions",
        headers={"Authorization": f"Bearer {token}"},
        json=reviewed_questions,
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "reviewed"

    assets_payload = [
        {
            "id": "manual-option-asset",
            "kind": "ocr_placeholder",
            "source": "manual",
            "status": "manual_review",
            "note": "人工补充的选项公式",
            "preview_url": None,
            "transcript": "公式图表示 x² 单调递增。",
            "target_question_number": 1,
            "target_field": "option_C",
        }
    ]
    saved_assets = client.put(
        f"/api/conversions/{conversion['id']}/assets",
        headers={"Authorization": f"Bearer {token}"},
        json=assets_payload,
    )
    assert saved_assets.status_code == 200

    exported = client.post(
        f"/api/conversions/{conversion['id']}/export/kshuati",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exported.status_code == 200
    export_text = exported.json()["export_text"]
    assert "1.下列说法正确的是" in export_text
    assert "\n()\n" in export_text
    assert "C.选项丙" in export_text
    assert "[manual] 公式图表示 x² 单调递增。" in export_text
    assert "答案:C" in export_text
    assert "解析:人工校对后的解析" in export_text


def test_conversion_api_deletes_history_item(tmp_path: Path):
    client = TestClient(app)
    token = register_and_login(client)
    paper_path = tmp_path / "delete-me.txt"
    paper_path.write_text(
        "1. 下列说法正确的是（ ）\nA. 甲\nB. 乙\nC. 丙\nD. 丁\n答案: A",
        encoding="utf-8",
    )

    with paper_path.open("rb") as file:
        created = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            data={"subject": "politics"},
            files={"file": ("delete-me.txt", file, "text/plain")},
        )

    assert created.status_code == 201
    conversion_id = created.json()["id"]

    deleted = client.delete(
        f"/api/conversions/{conversion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True}
    history = client.get("/api/conversions", headers={"Authorization": f"Bearer {token}"})
    assert all(item["id"] != conversion_id for item in history.json())
    detail = client.get(
        f"/api/conversions/{conversion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == 404


def test_conversion_api_rejects_legacy_doc_when_converter_is_missing(tmp_path: Path, monkeypatch):
    client = TestClient(app)
    token = register_and_login(client)
    doc_path = tmp_path / "legacy.doc"
    doc_path.write_bytes(b"legacy word content")
    monkeypatch.setattr("backend.app.conversions.shutil.which", lambda _name: None)

    with doc_path.open("rb") as file:
        response = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            data={"subject": "politics"},
            files={"file": ("legacy.doc", file, "application/msword")},
    )

    assert response.status_code == 415
    assert "LibreOffice" in response.json()["detail"]


def test_doc_extraction_uses_converted_docx_when_converter_exists(tmp_path: Path, monkeypatch):
    from backend.app.conversions import extract_text

    doc_path = tmp_path / "legacy.doc"
    doc_path.write_bytes(b"legacy word content")

    monkeypatch.setattr("backend.app.conversions.shutil.which", lambda _name: "soffice")

    def fake_run(command, capture_output, text, timeout, check):
        output_dir = Path(command[command.index("--outdir") + 1])
        converted_path = output_dir / "legacy.docx"
        document_xml = """
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:p><w:r><w:t>1.转换后的题目（ ）</w:t></w:r></w:p>
            <w:p><w:r><w:t>A.甲</w:t></w:r></w:p>
            <w:p><w:r><w:t>B.乙</w:t></w:r></w:p>
            <w:p><w:r><w:t>C.丙</w:t></w:r></w:p>
            <w:p><w:r><w:t>D.丁</w:t></w:r></w:p>
            <w:p><w:r><w:t>答案:A</w:t></w:r></w:p>
          </w:body>
        </w:document>
        """
        with zipfile.ZipFile(converted_path, "w") as archive:
            archive.writestr("word/document.xml", document_xml)

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return Completed()

    monkeypatch.setattr("backend.app.conversions.subprocess.run", fake_run)

    text, issues, assets = extract_text(doc_path)

    assert "转换后的题目" in text
    assert any("已通过 LibreOffice 转换" in issue for issue in issues)
    assert assets == []


def test_conversion_api_upload_docx_with_formula_placeholder_exports_after_review(tmp_path: Path):
    client = TestClient(app)
    token = register_and_login(client)
    docx_path = tmp_path / "formula-choice.docx"
    document_xml = """
    <w:document
      xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
      xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <w:body>
        <w:p>
          <w:r><w:t>1.函数</w:t></w:r>
          <m:oMathPara>
            <m:oMath><m:r><m:t>y=x^2</m:t></m:r></m:oMath>
          </m:oMathPara>
          <w:r><w:t>的图像是（ ）</w:t></w:r>
        </w:p>
        <w:p><w:r><w:t>A.直线</w:t></w:r></w:p>
        <w:p><w:r><w:t>B.抛物线</w:t></w:r></w:p>
        <w:p><w:r><w:t>C.双曲线</w:t></w:r></w:p>
        <w:p><w:r><w:t>D.圆</w:t></w:r></w:p>
        <w:p><w:r><w:t>答案:B</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    with docx_path.open("rb") as file:
        created = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            data={"subject": "math"},
            files={
                "file": (
                    "formula-choice.docx",
                    file,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert created.status_code == 201
    payload = created.json()
    assert payload["question_count"] == 1
    assert "DOCX 包含公式对象" in payload["issues"][0]
    assert payload["assets"][0]["source"] == "docx_formula"
    assert payload["assets"][0]["marker"] == "[公式1]"
    assert payload["assets"][0]["target_question_number"] == 1
    assert payload["assets"][0]["target_field"] == "stem"
    assert payload["questions"][0]["stem"] == "函数[公式1]的图像是（ ）"

    assets_payload = payload["assets"]
    assets_payload[0]["transcript"] = "y=x²"
    saved_assets = client.put(
        f"/api/conversions/{payload['id']}/assets",
        headers={"Authorization": f"Bearer {token}"},
        json=assets_payload,
    )
    assert saved_assets.status_code == 200

    exported = client.post(
        f"/api/conversions/{payload['id']}/export/kshuati",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert exported.status_code == 200
    assert "1.函数[formula-1] y=x²的图像是\n()" in exported.json()["export_text"]
    assert "答案:B" in exported.json()["export_text"]


def test_conversion_api_upload_docx_with_inline_image_marker_exports(tmp_path: Path):
    client = TestClient(app)
    token = register_and_login(client)
    docx_path = tmp_path / "image-choice.docx"
    document_xml = """
    <w:document
      xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <w:body>
        <w:p>
          <w:r><w:t>1.观察</w:t></w:r>
          <w:r><w:drawing><a:blip r:embed="rId1" /></w:drawing></w:r>
          <w:r><w:t>，下列正确的是（ ）</w:t></w:r>
        </w:p>
        <w:p><w:r><w:t>A.选项甲</w:t></w:r></w:p>
        <w:p><w:r><w:t>B.选项乙</w:t></w:r></w:p>
        <w:p><w:r><w:t>C.选项丙</w:t></w:r></w:p>
        <w:p><w:r><w:t>D.选项丁</w:t></w:r></w:p>
        <w:p><w:r><w:t>答案:A</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    rels_xml = """
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png" />
    </Relationships>
    """
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", rels_xml)
        archive.writestr("word/media/image1.png", b"fake-image")

    with docx_path.open("rb") as file:
        created = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            data={"subject": "biology"},
            files={
                "file": (
                    "image-choice.docx",
                    file,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert created.status_code == 201
    payload = created.json()
    assert payload["question_count"] == 1
    assert payload["questions"][0]["stem"] == "观察[图片1]，下列正确的是（ ）"
    assert payload["assets"][0]["filename"] == "image1.png"
    assert payload["assets"][0]["marker"] == "[图片1]"
    assert payload["assets"][0]["target_question_number"] == 1
    assert payload["assets"][0]["target_field"] == "stem"
    assert payload["assets"][0]["preview_url"]

    assets_payload = payload["assets"]
    assets_payload[0]["transcript"] = "图中叶绿体呈椭圆形。"
    saved_assets = client.put(
        f"/api/conversions/{payload['id']}/assets",
        headers={"Authorization": f"Bearer {token}"},
        json=assets_payload,
    )
    assert saved_assets.status_code == 200

    exported = client.post(
        f"/api/conversions/{payload['id']}/export/kshuati",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert exported.status_code == 200
    assert "1.观察[image1.png] 图中叶绿体呈椭圆形。，下列正确的是\n()" in exported.json()["export_text"]
    assert "答案:A" in exported.json()["export_text"]


def test_text_conversion_api_creates_task_from_pasted_text():
    client = TestClient(app)
    token = register_and_login(client)

    created = client.post(
        "/api/conversions/text",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "OCR 粘贴文本",
            "subject": "math",
            "text": "1.函数 y=x^2 的图像是（ ） A.直线 B.抛物线 C.双曲线 D.圆 答案:B",
        },
    )

    assert created.status_code == 201
    payload = created.json()
    assert payload["filename"] == "OCR 粘贴文本"
    assert payload["subject"] == "math"
    assert payload["raw_text"] == "1.函数 y=x^2 的图像是（ ） A.直线 B.抛物线 C.双曲线 D.圆 答案:B"
    assert payload["question_count"] == 1
    assert payload["questions"][0]["answer"] == "B"
    assert payload["questions"][0]["options"]["B"] == "抛物线"

    exported = client.post(
        f"/api/conversions/{payload['id']}/export/kshuati",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert exported.status_code == 200
    assert "函数 y=x² 的图像是" in exported.json()["export_text"]
    assert "答案:B" in exported.json()["export_text"]


def test_update_questions_recomputes_issues_after_manual_review(tmp_path: Path):
    client = TestClient(app)
    token = register_and_login(client)
    paper_path = tmp_path / "incomplete-choice.txt"
    paper_path.write_text(
        """
1. 补全这道题，本题用于验证人工校对后提示会重新计算，不再保留已经修复的问题
A. 选项甲
B. 选项乙
C. 选项丙
""".strip(),
        encoding="utf-8",
    )

    with paper_path.open("rb") as file:
        created = client.post(
            "/api/conversions",
            headers={"Authorization": f"Bearer {token}"},
            data={"subject": "politics"},
            files={"file": ("incomplete-choice.txt", file, "text/plain")},
        )

    assert created.status_code == 201
    conversion = created.json()
    assert conversion["issue_count"] == 2
    assert "第1题：缺少D选项" in conversion["issues"]
    assert "第1题：缺少答案" in conversion["issues"]

    questions = conversion["questions"]
    questions[0]["options"]["D"] = "选项丁"
    questions[0]["answer"] = "D"
    reviewed = client.put(
        f"/api/conversions/{conversion['id']}/questions",
        headers={"Authorization": f"Bearer {token}"},
        json=questions,
    )

    assert reviewed.status_code == 200
    payload = reviewed.json()
    assert payload["issue_count"] == 0
    assert payload["issues"] == []
    assert payload["questions"][0]["issues"] == []
