from __future__ import annotations

import json
import mimetypes
import sqlite3
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal, Protocol
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .auth import AuthUser, get_connection, get_current_user
from .kshuati_converter import (
    ParsedQuestion,
    Subject,
    detect_text_state,
    export_kshuati_text,
    parse_single_choice_questions,
    sorted_option_labels,
    validate_single_choice_question,
)

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency is optional at runtime
    PdfReader = None


router = APIRouter(prefix="/api/conversions", tags=["conversions"])

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
MEDIA_DIR = Path(__file__).resolve().parent / "conversion_media"
ALLOWED_SUFFIXES = {".pdf", ".docx", ".doc", ".txt"}


class ConversionQuestionPayload(BaseModel):
    number: int = Field(ge=1)
    stem: str = Field(default="", max_length=5000)
    options: dict[str, str] = Field(default_factory=dict)
    answer: str = Field(default="", max_length=1)
    analysis: str = Field(default="", max_length=5000)
    issues: list[str] = Field(default_factory=list)


class ConversionAssetPayload(BaseModel):
    id: str
    kind: Literal["image", "scan_page", "ocr_placeholder"]
    source: str
    status: Literal["pending_ocr", "manual_review", "unsupported"]
    note: str
    marker: str | None = None
    page: int | None = None
    filename: str | None = None
    stored_path: str | None = None
    mime_type: str | None = None
    preview_url: str | None = None
    transcript: str = Field(default="", max_length=5000)
    target_question_number: int | None = Field(default=None, ge=1)
    target_field: Literal[
        "stem",
        "analysis",
        "option_A",
        "option_B",
        "option_C",
        "option_D",
    ] = "stem"


class ConversionSummary(BaseModel):
    id: str
    filename: str
    subject: Subject
    status: str
    question_count: int
    issue_count: int
    created_at: str
    updated_at: str


class ConversionDetail(ConversionSummary):
    text_state: str
    raw_text: str
    issues: list[str]
    questions: list[ConversionQuestionPayload]
    assets: list[ConversionAssetPayload] = Field(default_factory=list)
    export_text: str | None = None


class ConversionExportResponse(BaseModel):
    export_text: str
    question_count: int
    issues: list[str]


class TextConversionRequest(BaseModel):
    title: str = Field(default="粘贴文本", max_length=120)
    text: str = Field(min_length=1, max_length=200000)
    subject: Subject = "general"


class OcrAssetResponse(BaseModel):
    asset: ConversionAssetPayload
    message: str


class OcrResult(BaseModel):
    transcript: str = ""
    message: str
    provider: str
    available: bool = True


class OcrProvider(Protocol):
    name: str

    def recognize(self, image_path: Path, subject: Subject) -> OcrResult:
        ...


class TesseractOcrProvider:
    name = "tesseract"

    def recognize(self, image_path: Path, subject: Subject) -> OcrResult:
        executable = shutil.which("tesseract")
        if not executable:
            return OcrResult(
                transcript="",
                message="当前环境未安装 Tesseract OCR，已保留人工转写入口。",
                provider=self.name,
                available=False,
            )

        languages = "chi_sim+eng"
        if subject in {"math", "physics", "chemistry", "biology"}:
            languages = "eng+chi_sim"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_base = Path(temp_dir) / "ocr-output"
            command = [executable, str(image_path), str(output_base), "-l", languages, "--psm", "6"]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
            if completed.returncode != 0:
                message = completed.stderr.strip() or "OCR 执行失败。"
                return OcrResult(transcript="", message=message, provider=self.name)

            output_path = output_base.with_suffix(".txt")
            if not output_path.exists():
                return OcrResult(transcript="", message="OCR 未生成文本结果。", provider=self.name)
            return OcrResult(
                transcript=output_path.read_text(encoding="utf-8", errors="ignore").strip(),
                message="OCR 已完成，请校对识别结果。",
                provider=self.name,
            )


def get_ocr_provider(_subject: Subject) -> OcrProvider:
    return TesseractOcrProvider()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_conversion_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                stored_path TEXT,
                source_type TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT 'general',
                raw_text TEXT NOT NULL DEFAULT '',
                text_state TEXT NOT NULL DEFAULT 'text',
                status TEXT NOT NULL,
                questions_json TEXT NOT NULL DEFAULT '[]',
                issues_json TEXT NOT NULL DEFAULT '[]',
                assets_json TEXT NOT NULL DEFAULT '[]',
                export_text TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(conversions)").fetchall()
        }
        if "assets_json" not in columns:
            connection.execute("ALTER TABLE conversions ADD COLUMN assets_json TEXT NOT NULL DEFAULT '[]'")
        if "subject" not in columns:
            connection.execute("ALTER TABLE conversions ADD COLUMN subject TEXT NOT NULL DEFAULT 'general'")


def row_to_summary(row: sqlite3.Row) -> ConversionSummary:
    questions = read_json(row["questions_json"], [])
    issues = collect_issue_list(row)
    return ConversionSummary(
        id=row["id"],
        filename=row["filename"],
        subject=row["subject"] if row["subject"] else "general",
        status=row["status"],
        question_count=len(questions),
        issue_count=len(issues),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_detail(row: sqlite3.Row) -> ConversionDetail:
    questions = read_json(row["questions_json"], [])
    assets = read_json(row["assets_json"], [])
    issues = collect_issue_list(row)
    summary = row_to_summary(row)
    return ConversionDetail(
        **summary.model_dump(),
        text_state=row["text_state"],
        raw_text=row["raw_text"],
        issues=issues,
        questions=[ConversionQuestionPayload(**question) for question in questions],
        assets=[ConversionAssetPayload(**asset) for asset in assets],
        export_text=row["export_text"],
    )


def read_json(value: str, fallback):
    try:
        parsed = json.loads(value or "")
    except json.JSONDecodeError:
        return fallback
    return parsed if isinstance(parsed, type(fallback)) else fallback


def question_to_payload(question: ParsedQuestion) -> dict[str, object]:
    return {
        "number": question.number,
        "stem": question.stem,
        "options": {key: question.options.get(key, "") for key in sorted_option_labels(question.options)},
        "answer": question.answer,
        "analysis": question.analysis,
        "issues": question.issues,
    }


def payload_to_question(payload: ConversionQuestionPayload) -> ParsedQuestion:
    return ParsedQuestion(
        number=payload.number,
        stem=payload.stem.strip(),
        options={key.upper(): value.strip() for key, value in payload.options.items()},
        answer=payload.answer.strip().upper(),
        analysis=payload.analysis.strip(),
        issues=list(payload.issues),
    )


def apply_asset_transcripts(
    questions: list[ParsedQuestion],
    assets: list[ConversionAssetPayload],
) -> None:
    question_by_number = {question.number: question for question in questions}

    for asset in assets:
        transcript = asset.transcript.strip()
        if not transcript or not asset.target_question_number:
            continue

        question = question_by_number.get(asset.target_question_number)
        if question is None:
            continue

        prefix = f"[{asset.filename or asset.source}] "
        inserted_text = f"{prefix}{transcript}"
        if asset.target_field == "analysis":
            if asset.marker and asset.marker in question.analysis:
                question.analysis = question.analysis.replace(asset.marker, inserted_text)
            else:
                question.analysis = "\n".join(part for part in [question.analysis, inserted_text] if part)
        elif asset.target_field.startswith("option_"):
            label = asset.target_field.removeprefix("option_")
            option_text = question.options.get(label, "")
            if asset.marker and asset.marker in option_text:
                question.options[label] = option_text.replace(asset.marker, inserted_text)
            else:
                question.options[label] = "\n".join(part for part in [option_text, inserted_text] if part)
        else:
            if asset.marker and asset.marker in question.stem:
                question.stem = question.stem.replace(asset.marker, inserted_text)
            else:
                question.stem = "\n".join(part for part in [question.stem, inserted_text] if part)


def bind_assets_to_detected_markers(
    assets: list[dict[str, object]],
    questions: list[ParsedQuestion],
) -> list[dict[str, object]]:
    bound_assets: list[dict[str, object]] = []
    for asset in assets:
        asset_copy = dict(asset)
        marker = str(asset_copy.get("marker") or "")
        if not marker or asset_copy.get("target_question_number"):
            bound_assets.append(asset_copy)
            continue

        for question in questions:
            if marker in question.stem:
                asset_copy["target_question_number"] = question.number
                asset_copy["target_field"] = "stem"
                break
            if marker in question.analysis:
                asset_copy["target_question_number"] = question.number
                asset_copy["target_field"] = "analysis"
                break
            matched_option = next(
                (label for label, value in question.options.items() if marker in value),
                "",
            )
            if matched_option:
                asset_copy["target_question_number"] = question.number
                asset_copy["target_field"] = f"option_{matched_option}"
                break

        bound_assets.append(asset_copy)
    return bound_assets


def normalize_asset_payload(conversion_id: str, asset: ConversionAssetPayload) -> dict[str, object]:
    data = asset.model_dump()
    data["transcript"] = data["transcript"].strip()
    data["preview_url"] = (
        f"/api/conversions/{conversion_id}/assets/{data['id']}/preview"
        if data.get("stored_path")
        else None
    )
    if data["transcript"] and data["status"] == "pending_ocr":
        data["status"] = "manual_review"
    return data


def run_tesseract_ocr(image_path: Path, subject: Subject) -> tuple[str, str]:
    result = TesseractOcrProvider().recognize(image_path, subject)
    return result.transcript, result.message


def collect_issue_list(row: sqlite3.Row) -> list[str]:
    task_issues = read_json(row["issues_json"], [])
    question_issues: list[str] = []
    for question in read_json(row["questions_json"], []):
        number = question.get("number", "?") if isinstance(question, dict) else "?"
        for issue in question.get("issues", []) if isinstance(question, dict) else []:
            question_issues.append(f"第{number}题：{issue}")
    return [*task_issues, *question_issues]


def make_asset(
    kind: Literal["image", "scan_page", "ocr_placeholder"],
    source: str,
    status_value: Literal["pending_ocr", "manual_review", "unsupported"],
    note: str,
    marker: str | None = None,
    page: int | None = None,
    filename: str | None = None,
    stored_path: str | None = None,
    mime_type: str | None = None,
    transcript: str = "",
) -> dict[str, object]:
    asset_id = str(uuid.uuid4())
    return {
        "id": asset_id,
        "kind": kind,
        "source": source,
        "status": status_value,
        "note": note,
        "marker": marker,
        "page": page,
        "filename": filename,
        "stored_path": stored_path,
        "mime_type": mime_type,
        "preview_url": None,
        "transcript": transcript,
        "target_question_number": None,
        "target_field": "stem",
    }


def ocr_placeholder(source: str, note: str, page: int | None = None) -> dict[str, object]:
    return make_asset(
        kind="ocr_placeholder",
        source=source,
        status_value="pending_ocr",
        note=note,
        page=page,
    )


def with_preview_urls(conversion_id: str, assets: list[dict[str, object]]) -> list[dict[str, object]]:
    updated_assets = []
    for asset in assets:
        asset_copy = dict(asset)
        if asset_copy.get("stored_path"):
            asset_copy["preview_url"] = f"/api/conversions/{conversion_id}/assets/{asset_copy.get('id')}/preview"
        else:
            asset_copy["preview_url"] = None
        updated_assets.append(asset_copy)
    return updated_assets


async def save_upload(file: UploadFile, user_id: str) -> Path:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="仅支持 PDF、DOC、DOCX 和 TXT 文件。",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIR / f"{user_id}-{uuid.uuid4().hex}{suffix}"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上传文件为空。")
    stored_path.write_bytes(content)
    return stored_path


def extract_text(
    path: Path,
    conversion_id: str | None = None,
    include_assets: bool = True,
) -> tuple[str, list[str], list[dict[str, object]]]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8-sig"), [], []
    if suffix == ".doc":
        converted_path, issues = convert_doc_to_docx(path)
        text, extraction_issues, assets = extract_docx_text(
            converted_path,
            conversion_id=conversion_id,
            include_assets=include_assets,
        )
        return text, [*issues, *extraction_issues], assets
    if suffix == ".docx":
        return extract_docx_text(path, conversion_id=conversion_id, include_assets=include_assets)
    if suffix == ".pdf":
        return extract_pdf_text(path, conversion_id=conversion_id, include_assets=include_assets)
    raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="不支持的文件格式。")


def convert_doc_to_docx(path: Path) -> tuple[Path, list[str]]:
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if not executable:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="旧版 .doc 需要 LibreOffice/soffice 转换器。当前环境未检测到转换器，请用 Word/WPS 另存为 .docx，或复制文档内容粘贴解析。",
        )

    output_dir = path.parent / f"{path.stem}-converted-{uuid.uuid4().hex}"
    output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            executable,
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            str(output_dir),
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    converted_path = output_dir / f"{path.stem}.docx"
    if completed.returncode != 0 or not converted_path.exists():
        message = completed.stderr.strip() or completed.stdout.strip() or "旧版 .doc 转换失败。"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{message} 请用 Word/WPS 另存为 .docx 后重试。",
        )
    return converted_path, ["旧版 .doc 已通过 LibreOffice 转换为 .docx 后解析。"]


def save_media_asset(
    conversion_id: str | None,
    filename: str,
    data: bytes,
) -> Path | None:
    if not conversion_id:
        return None

    media_dir = MEDIA_DIR / conversion_id
    media_dir.mkdir(parents=True, exist_ok=True)
    stored_path = media_dir / f"{uuid.uuid4().hex}-{Path(filename).name}"
    stored_path.write_bytes(data)
    return stored_path


def extract_pdf_text(
    path: Path,
    conversion_id: str | None = None,
    include_assets: bool = True,
) -> tuple[str, list[str], list[dict[str, object]]]:
    if PdfReader is None:
        return "", ["当前环境缺少 pypdf，无法读取 PDF 文本。"], [
            ocr_placeholder("pdf", "PDF 文本读取失败时可交由 OCR Provider 处理。")
        ]

    try:
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as error:  # pragma: no cover - library raises many concrete types
        return "", [f"PDF 读取失败：{error}"], [
            ocr_placeholder("pdf", "PDF 读取异常，后续可交由 OCR Provider 处理。")
        ]

    text = "\n".join(page for page in pages if page)
    issues = []
    assets: list[dict[str, object]] = []
    if include_assets:
        for index, page_text in enumerate(pages, 1):
            page = reader.pages[index - 1]
            try:
                page_images = list(getattr(page, "images", []) or [])
            except Exception:
                page_images = []

            for image_index, image in enumerate(page_images, 1):
                image_name = getattr(image, "name", f"page-{index}-image-{image_index}.bin")
                image_data = getattr(image, "data", b"")
                if not image_data:
                    continue
                stored_media_path = save_media_asset(conversion_id, image_name, image_data)
                assets.append(
                    make_asset(
                        kind="image",
                        source="pdf",
                        status_value="pending_ocr",
                        note=f"PDF 第 {index} 页内嵌图片，可能包含公式、图表或题目内容。",
                        page=index,
                        filename=image_name,
                        stored_path=str(stored_media_path) if stored_media_path else None,
                        mime_type=mimetypes.guess_type(image_name)[0] or "application/octet-stream",
                    )
                )

            if not page_text:
                assets.append(
                    make_asset(
                        kind="scan_page",
                        source="pdf",
                        status_value="pending_ocr",
                        note="该页未提取到文字，疑似扫描页或图片页。",
                        page=index,
                    )
                )

    if include_assets and not text.strip():
        issues.append("未从 PDF 提取到文字，可能是扫描件或图片型 PDF，OCR 接口已预留但尚未启用。")
    elif include_assets and any(asset.get("kind") == "scan_page" for asset in assets):
        issues.append("PDF 中存在未提取出文字的页面，已作为待 OCR 页面记录。")
    return text, issues, assets


def extract_docx_text(
    path: Path,
    conversion_id: str | None = None,
    include_assets: bool = True,
) -> tuple[str, list[str], list[dict[str, object]]]:
    paragraphs: list[str] = []
    issues: list[str] = []
    assets: list[dict[str, object]] = []
    namespace = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    }

    try:
        with zipfile.ZipFile(path) as archive:
            document = archive.read("word/document.xml")
            media_files = [name for name in archive.namelist() if name.startswith("word/media/")]
            try:
                rels_document = archive.read("word/_rels/document.xml.rels")
            except KeyError:
                rels_document = b""
    except (KeyError, zipfile.BadZipFile) as error:
        return "", [f"DOCX 读取失败：{error}"], [
            ocr_placeholder("docx", "DOCX 读取失败，无法抽取内嵌文本或图片。")
        ]

    relationship_targets: dict[str, str] = {}
    if rels_document:
        rels_root = ElementTree.fromstring(rels_document)
        for relationship in rels_root.findall(".//rel:Relationship", namespace):
            relationship_id = relationship.attrib.get("Id", "")
            target = relationship.attrib.get("Target", "")
            if relationship_id and target:
                relationship_targets[relationship_id] = (
                    target if target.startswith("word/") else f"word/{target.lstrip('/')}"
                )

    root = ElementTree.fromstring(document)
    formula_index = 0
    image_index = 0
    used_media_files: set[str] = set()
    for paragraph in root.findall(".//w:p", namespace):
        text_parts: list[str] = []
        for child in paragraph.iter():
            if child.tag == f"{{{namespace['w']}}}t" and child.text:
                text_parts.append(child.text)
            elif child.tag == f"{{{namespace['m']}}}oMath":
                formula_index += 1
                formula_text = "".join(
                    node.text or "" for node in child.findall(".//m:t", namespace)
                ).strip()
                if include_assets:
                    marker = f"[公式{formula_index}]"
                    text_parts.append(marker)
                    assets.append(
                        make_asset(
                            kind="ocr_placeholder",
                            source="docx_formula",
                            status_value="manual_review",
                            note=f"DOCX 第 {formula_index} 个公式对象，已插入 {marker} 占位，请人工校对公式文本。",
                            marker=marker,
                            filename=f"formula-{formula_index}",
                            transcript=formula_text,
                        )
                    )
                elif formula_text:
                    text_parts.append(formula_text)
            elif child.tag == f"{{{namespace['a']}}}blip":
                if not include_assets:
                    continue
                relationship_id = child.attrib.get(f"{{{namespace['r']}}}embed", "")
                media_file = relationship_targets.get(relationship_id, "")
                if not media_file:
                    continue

                image_index += 1
                marker = f"[图片{image_index}]"
                text_parts.append(marker)
                used_media_files.add(media_file)
                media_filename = Path(media_file).name
                with zipfile.ZipFile(path) as archive:
                    stored_media_path = save_media_asset(
                        conversion_id,
                        media_filename,
                        archive.read(media_file),
                    )
                assets.append(
                    make_asset(
                        kind="image",
                        source="docx",
                        status_value="pending_ocr",
                        note=f"DOCX 图片 {marker}，已按原文位置插入占位，请 OCR 或人工转写后绑定到对应题目。",
                        marker=marker,
                        filename=media_filename,
                        stored_path=str(stored_media_path) if stored_media_path else None,
                        mime_type=mimetypes.guess_type(media_filename)[0] or "application/octet-stream",
                    )
                )
        text = "".join(text_parts).strip()
        if text:
            paragraphs.append(text)

    if include_assets and formula_index:
        issues.append("DOCX 包含公式对象，已插入公式占位并标记为待人工校对。")

    if include_assets and media_files:
        issues.append("DOCX 包含图片，图片内容已标记为待人工处理，OCR 接口尚未启用。")
        for media_file in media_files:
            if media_file in used_media_files:
                continue
            media_filename = Path(media_file).name
            with zipfile.ZipFile(path) as archive:
                stored_media_path = save_media_asset(
                    conversion_id,
                    media_filename,
                    archive.read(media_file),
                )

            assets.append(
                make_asset(
                    kind="image",
                    source="docx",
                    status_value="pending_ocr",
                    note="DOCX 内嵌图片，可能包含题干、图表、公式或选项。",
                    filename=media_filename,
                    stored_path=str(stored_media_path) if stored_media_path else None,
                    mime_type=mimetypes.guess_type(media_filename)[0] or "application/octet-stream",
                )
            )

    text = "\n".join(paragraphs)
    if include_assets and not text.strip():
        issues.append("未从 DOCX 提取到文字，可能主要由图片构成。")
    return text, issues, assets


def create_conversion_record(
    *,
    user_id: str,
    filename: str,
    source_type: str,
    subject: Subject,
    raw_text: str,
    extraction_issues: list[str] | None = None,
    assets: list[dict[str, object]] | None = None,
    stored_path: str | None = None,
    conversion_id: str | None = None,
    include_assets: bool = True,
) -> ConversionDetail:
    conversion_id = conversion_id or str(uuid.uuid4())
    issues = list(extraction_issues or [])
    asset_payloads = list(assets or [])
    text_state = detect_text_state(raw_text)
    if include_assets and text_state == "needs_ocr":
        issues.append("文本量过少，疑似扫描件或图片题，请人工校对或等待 OCR 接入。")
        asset_payloads.append(ocr_placeholder(source_type, "文本量过少，建议进入 OCR 识别流程。"))
    if text_state == "empty":
        issues.append("未提取到可解析文本。")
        if include_assets:
            asset_payloads.append(ocr_placeholder(source_type, "未提取到文本，建议进入 OCR 识别流程。"))

    parsed_questions = parse_single_choice_questions(raw_text, subject=subject)
    question_payloads = [question_to_payload(question) for question in parsed_questions]
    asset_payloads = bind_assets_to_detected_markers(asset_payloads, parsed_questions)
    if not question_payloads:
        issues.append("未识别到单选题结构，请检查题号和选项格式。")

    now = utc_now()
    status_value = "needs_review" if question_payloads else "needs_attention"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversions (
                id, user_id, filename, stored_path, source_type, subject, raw_text, text_state,
                status, questions_json, issues_json, assets_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversion_id,
                user_id,
                filename,
                stored_path,
                source_type,
                subject,
                raw_text,
                text_state,
                status_value,
                json.dumps(question_payloads, ensure_ascii=False),
                json.dumps(issues, ensure_ascii=False),
                json.dumps(with_preview_urls(conversion_id, asset_payloads), ensure_ascii=False),
                now,
                now,
            ),
        )
        row = connection.execute(
            "SELECT * FROM conversions WHERE id = ? AND user_id = ?",
            (conversion_id, user_id),
        ).fetchone()

    return row_to_detail(row)


@router.post("", response_model=ConversionDetail, status_code=status.HTTP_201_CREATED)
async def create_conversion(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    file: UploadFile = File(...),
    subject: Subject = Form("general"),
    include_assets: bool = Form(True),
) -> ConversionDetail:
    stored_path = await save_upload(file, current_user.id)
    conversion_id = str(uuid.uuid4())
    raw_text, extraction_issues, assets = extract_text(
        stored_path,
        conversion_id=conversion_id,
        include_assets=include_assets,
    )
    return create_conversion_record(
        user_id=current_user.id,
        filename=file.filename or stored_path.name,
        stored_path=str(stored_path),
        source_type=stored_path.suffix.lower().removeprefix("."),
        subject=subject,
        raw_text=raw_text,
        extraction_issues=extraction_issues,
        assets=assets,
        conversion_id=conversion_id,
        include_assets=include_assets,
    )


@router.post("/text", response_model=ConversionDetail, status_code=status.HTTP_201_CREATED)
def create_text_conversion(
    payload: TextConversionRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> ConversionDetail:
    return create_conversion_record(
        user_id=current_user.id,
        filename=payload.title.strip() or "粘贴文本",
        stored_path=None,
        source_type="text",
        subject=payload.subject,
        raw_text=payload.text,
    )


@router.get("", response_model=list[ConversionSummary])
def list_conversions(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> list[ConversionSummary]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM conversions
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC
            """,
            (current_user.id,),
        ).fetchall()
    return [row_to_summary(row) for row in rows]


@router.get("/{conversion_id}", response_model=ConversionDetail)
def get_conversion(
    conversion_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> ConversionDetail:
    row = find_conversion(conversion_id, current_user.id)
    return row_to_detail(row)


@router.put("/{conversion_id}/questions", response_model=ConversionDetail)
def update_questions(
    conversion_id: str,
    payload: list[ConversionQuestionPayload],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> ConversionDetail:
    find_conversion(conversion_id, current_user.id)
    normalized = []
    for index, question in enumerate(payload, 1):
        data = question.model_dump()
        data["number"] = index
        data["answer"] = data["answer"].strip().upper()
        data["options"] = {
            key.upper(): value.strip()
            for key, value in data["options"].items()
            if key.strip()
        }
        data["issues"] = validate_single_choice_question(
            ParsedQuestion(
                number=data["number"],
                stem=data["stem"].strip(),
                options=data["options"],
                answer=data["answer"],
                analysis=data["analysis"].strip(),
            )
        )
        normalized.append(data)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE conversions
            SET questions_json = ?, export_text = NULL, status = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                json.dumps(normalized, ensure_ascii=False),
                "reviewed",
                utc_now(),
                conversion_id,
                current_user.id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM conversions WHERE id = ? AND user_id = ?",
            (conversion_id, current_user.id),
        ).fetchone()
    return row_to_detail(row)


@router.put("/{conversion_id}/assets", response_model=ConversionDetail)
def update_assets(
    conversion_id: str,
    payload: list[ConversionAssetPayload],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> ConversionDetail:
    find_conversion(conversion_id, current_user.id)
    normalized = []
    for asset in payload:
        normalized.append(normalize_asset_payload(conversion_id, asset))

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE conversions
            SET assets_json = ?, export_text = NULL, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                json.dumps(normalized, ensure_ascii=False),
                utc_now(),
                conversion_id,
                current_user.id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM conversions WHERE id = ? AND user_id = ?",
            (conversion_id, current_user.id),
        ).fetchone()
    return row_to_detail(row)


@router.post("/{conversion_id}/assets/{asset_id}/ocr", response_model=OcrAssetResponse)
def ocr_asset(
    conversion_id: str,
    asset_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> OcrAssetResponse:
    row = find_conversion(conversion_id, current_user.id)
    assets = [ConversionAssetPayload(**item) for item in read_json(row["assets_json"], [])]
    asset_index = next((index for index, item in enumerate(assets) if item.id == asset_id), None)
    if asset_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="素材不存在。")

    asset = assets[asset_index]
    if not asset.stored_path:
        asset.status = "unsupported"
        message = "该素材没有可识别的图片文件，请人工转写。"
    else:
        image_path = Path(asset.stored_path).resolve()
        media_root = MEDIA_DIR.resolve()
        if media_root not in image_path.parents or not image_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="素材文件不存在。")

        provider = get_ocr_provider(row["subject"] or "general")
        result = provider.recognize(image_path, row["subject"] or "general")
        message = result.message
        if result.transcript:
            asset.transcript = result.transcript
            asset.status = "manual_review"
        else:
            asset.status = "unsupported"

    normalized_assets = [
        normalize_asset_payload(conversion_id, item) for item in assets
    ]
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE conversions
            SET assets_json = ?, export_text = NULL, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                json.dumps(normalized_assets, ensure_ascii=False),
                utc_now(),
                conversion_id,
                current_user.id,
            ),
        )

    return OcrAssetResponse(
        asset=ConversionAssetPayload(**normalized_assets[asset_index]),
        message=message,
    )


@router.get("/{conversion_id}/assets/{asset_id}/preview")
def preview_asset(
    conversion_id: str,
    asset_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> FileResponse:
    row = find_conversion(conversion_id, current_user.id)
    assets = [ConversionAssetPayload(**item) for item in read_json(row["assets_json"], [])]
    asset = next((item for item in assets if item.id == asset_id), None)
    if asset is None or not asset.stored_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="素材不存在或不可预览。")

    path = Path(asset.stored_path).resolve()
    media_root = MEDIA_DIR.resolve()
    if media_root not in path.parents:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="素材路径无效。")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="素材文件不存在。")

    return FileResponse(
        path,
        media_type=asset.mime_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        filename=asset.filename or path.name,
    )


@router.delete("/{conversion_id}")
def delete_conversion(
    conversion_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, bool]:
    row = find_conversion(conversion_id, current_user.id)
    stored_path = row["stored_path"]

    with get_connection() as connection:
        connection.execute(
            "DELETE FROM conversions WHERE id = ? AND user_id = ?",
            (conversion_id, current_user.id),
        )

    if stored_path:
        path = Path(stored_path)
        if path.exists() and path.is_file():
            path.unlink()

    media_dir = MEDIA_DIR / conversion_id
    if media_dir.exists():
        shutil.rmtree(media_dir)

    return {"deleted": True}


@router.post("/{conversion_id}/export/kshuati", response_model=ConversionExportResponse)
def export_conversion(
    conversion_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> ConversionExportResponse:
    row = find_conversion(conversion_id, current_user.id)
    question_payloads = [ConversionQuestionPayload(**item) for item in read_json(row["questions_json"], [])]
    asset_payloads = [ConversionAssetPayload(**item) for item in read_json(row["assets_json"], [])]
    questions = [payload_to_question(payload) for payload in question_payloads]
    apply_asset_transcripts(questions, asset_payloads)
    export_text = export_kshuati_text(questions, subject=row["subject"] or "general")

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE conversions
            SET export_text = ?, status = 'exported', updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (export_text, utc_now(), conversion_id, current_user.id),
        )

    return ConversionExportResponse(
        export_text=export_text,
        question_count=len(questions),
        issues=collect_issue_list(row),
    )


def find_conversion(conversion_id: str, user_id: str) -> sqlite3.Row:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM conversions WHERE id = ? AND user_id = ?",
            (conversion_id, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="转换任务不存在。")
    return row
