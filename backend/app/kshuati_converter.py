from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Subject = Literal["general", "politics", "math", "physics", "chemistry", "biology"]

OPTION_LABEL_CHARS = "A-Za-zＡ-Ｚａ-ｚ"
OPTION_LABEL_ORDER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
OPTION_MARKER_RE = rf"(?:[{OPTION_LABEL_CHARS}]\s*[.．、:：)）]|\([{OPTION_LABEL_CHARS}]\)|（[{OPTION_LABEL_CHARS}]）|【[{OPTION_LABEL_CHARS}]】|\[[{OPTION_LABEL_CHARS}]\])"

QUESTION_NUMBER_RE = re.compile(r"^\s*(?:第\s*(\d+)\s*题\s*[:：、.)）]?|(\d+)\s*[.、)）])\s*(.*)$")
OPTION_RE = re.compile(
    rf"^\s*(?:([{OPTION_LABEL_CHARS}])(?:\s*[.．、:：)）]|\s+)|\(([{OPTION_LABEL_CHARS}])\)|（([{OPTION_LABEL_CHARS}])）|【([{OPTION_LABEL_CHARS}])】|\[([{OPTION_LABEL_CHARS}])\])\s*(.*)$"
)
ANSWER_RE = re.compile(rf"^\s*(?:【(?:答案|正确答案|参考答案)】|\[(?:答案|正确答案|参考答案)\]|(?:答案|正确答案|参考答案|Answer|Correct\s+Answer|Reference\s+Answer)\s*[:：]?)\s*([{OPTION_LABEL_CHARS}])\b\s*(.*)$", re.I)
ANALYSIS_RE = re.compile(r"^\s*(?:【(?:解析|答案解析|解题思路|说明)】|\[(?:解析|答案解析|解题思路|说明)\]|(?:解析|答案解析|解题思路|说明)\s*[:：])\s*(.*)$")
ANSWER_PLACEHOLDER_RE = re.compile(r"\s*(?:（\s*）|\(\s*\))\s*$")
CENTRAL_ANSWER_HEADER_RE = re.compile(r"^\s*(?:参考答案及解析|答案及解析|参考答案|正确答案|答案|Answers?|Answer\s+Key|Correct\s+Answers?)\s*[:：]?\s*(.*)$", re.I)
CENTRAL_ANSWER_PAIR_RE = re.compile(rf"(?:^|[\s,，;；、])(\d{{1,4}})\s*[.．、:：）)]?\s*([{OPTION_LABEL_CHARS}])\b")
CENTRAL_ANSWER_ITEM_RE = re.compile(
    rf"(?:^|[\s,，;；、])(\d{{1,4}})\s*[.．、:：）)]?\s*([{OPTION_LABEL_CHARS}])\b(.*?)(?=(?:[\s,，;；、]\d{{1,4}}\s*[.．、:：）)]?\s*[{OPTION_LABEL_CHARS}]\b)|$)",
    re.S,
)
CENTRAL_ANALYSIS_PREFIX_RE = re.compile(r"^\s*(?:解析|答案解析|解题思路|说明)\s*[:：]?\s*")

INLINE_ANALYSIS_MARKERS = ("解析:", "解析：", "解题思路:", "解题思路：", "说明:", "说明：")

CHAR_REPLACEMENTS = {
    "|": "｜",
    "、": "，",
}

SUPERSCRIPT_MAP = {
    "^(-1)": "⁻¹",
    "^(-2)": "⁻²",
    "^2": "²",
    "^3": "³",
    "^T": "ᵀ",
    "^t": "ᵀ",
}

COMPLEX_SUPERSCRIPT_RULES = [
    (re.compile(r"\^\(([^)]+)\)"), r"的\1次方"),
    (re.compile(r"\^(\w+)"), r"的\1次方"),
]

LATEX_REPLACEMENTS = {
    r"\times": "×",
    r"\cdot": "·",
    r"\div": "÷",
    r"\pm": "±",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\neq": "≠",
    r"\approx": "≈",
    r"\infty": "∞",
    r"\angle": "∠",
    r"\parallel": "∥",
    r"\perp": "⊥",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\theta": "θ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\pi": "π",
    r"\rho": "ρ",
    r"\sigma": "σ",
    r"\omega": "ω",
    r"\Delta": "Δ",
    r"\Omega": "Ω",
    r"\rightarrow": "→",
    r"\to": "→",
    r"\leftarrow": "←",
    r"\rightleftharpoons": "⇌",
}

SUBSCRIPT_DIGITS = str.maketrans("0123456789+-", "₀₁₂₃₄₅₆₇₈₉₊₋")


def replace_latex_fraction(match: re.Match[str]) -> str:
    numerator = match.group(1).strip()
    denominator = match.group(2).strip()
    return f"{numerator}/{denominator}"


def replace_subscript(match: re.Match[str]) -> str:
    value = match.group(1) or match.group(2) or ""
    if re.fullmatch(r"[0-9+-]+", value):
        return value.translate(SUBSCRIPT_DIGITS)
    return f"_{value}"


def normalize_option_label(value: str) -> str:
    label = value.strip()
    if not label:
        return ""

    char_code = ord(label[0])
    if ord("Ａ") <= char_code <= ord("Ｆ"):
        return chr(ord("A") + char_code - ord("Ａ"))
    if ord("ａ") <= char_code <= ord("ｆ"):
        return chr(ord("A") + char_code - ord("ａ"))
    return label[0].upper()


def first_present(*values: str | None) -> str:
    return next((value for value in values if value), "")


def split_inline_segments(text: str) -> list[str]:
    normalized = text
    normalized = re.sub(r"\r\n?", "\n", normalized)
    normalized = re.sub(r"(?<!\n)(?:(?<=^)|(?<=\s))(?=\d+\s*[.、）)]\s*\S)", "\n", normalized)
    normalized = re.sub(r"(?<!\n)(?:(?<=^)|(?<=\s))(?=第\s*\d+\s*题)", "\n", normalized)
    normalized = re.sub(
        rf"(?<!\n)(?:(?<=^)|(?<=\s))(?={OPTION_MARKER_RE}\s*\S)",
        "\n",
        normalized,
    )
    normalized = re.sub(
        r"(?<!\n)(?=A[.．、：:）)](?=[^\n]{1,120}B[.．、：:）)]))",
        "\n",
        normalized,
    )
    normalized = re.sub(
        r"(?<!\n)(?=a[.．、：:）)](?=[^\n]{1,120}b[.．、：:）)]))",
        "\n",
        normalized,
    )
    normalized = re.sub(
        r"(?<!\n)(?=Ａ[.．、：:）)](?=[^\n]{1,120}Ｂ[.．、：:）)]))",
        "\n",
        normalized,
    )
    for previous_label, next_label in (("A", "B"), ("B", "C"), ("C", "D")):
        normalized = re.sub(
            rf"({previous_label}[.．、：:）)][^\n]{{1,120}})(?={next_label}[.．、：:）)]\s*\S|\({next_label}\)|（{next_label}）)",
            r"\1\n",
            normalized,
        )
        normalized = re.sub(
            rf"({previous_label.lower()}[.．、：:）)][^\n]{{1,120}})(?={next_label.lower()}[.．、：:）)]\s*\S|\({next_label.lower()}\)|（{next_label.lower()}）)",
            r"\1\n",
            normalized,
        )
        normalized = re.sub(
            rf"({chr(ord('Ａ') + ord(previous_label) - ord('A'))}[.．、：:）)][^\n]{{1,120}})(?={chr(ord('Ａ') + ord(next_label) - ord('A'))}[.．、：:）)]\s*\S|（{chr(ord('Ａ') + ord(next_label) - ord('A'))}）)",
            r"\1\n",
            normalized,
        )
    normalized = re.sub(
        r"(?<!\n)(?:(?<=^)|(?<=\s))(?=(?:答案|参考答案|正确答案|Answer|Correct\s+Answer|Reference\s+Answer|解析|解题思路|说明)\s*[:：])",
        "\n",
        normalized,
        flags=re.I,
    )
    normalized = re.sub(
        r"(?<!\n)(?<![A-Za-zＡ-Ｚａ-ｚ])(?=(?:【(?:答案|正确答案|参考答案|解析|答案解析|解题思路|说明)】|\[(?:答案|正确答案|参考答案|解析|答案解析|解题思路|说明)\]|(?:答案|参考答案|正确答案|Answer|Correct\s+Answer|Reference\s+Answer|解析|解题思路|说明)\s*[:：]))",
        "\n",
        normalized,
        flags=re.I,
    )
    return [segment.strip() for segment in normalized.split("\n") if segment.strip()]


def parse_central_answer_pairs(value: str) -> dict[int, str]:
    return {
        int(match.group(1)): normalize_option_label(match.group(2))
        for match in CENTRAL_ANSWER_PAIR_RE.finditer(value)
    }


def parse_central_answer_details(value: str) -> tuple[dict[int, str], dict[int, str]]:
    answer_key: dict[int, str] = {}
    analysis_key: dict[int, str] = {}

    for match in CENTRAL_ANSWER_ITEM_RE.finditer(value):
        number = int(match.group(1))
        answer_key[number] = normalize_option_label(match.group(2))
        analysis = CENTRAL_ANALYSIS_PREFIX_RE.sub("", match.group(3).strip(" ，,;；、"))
        if analysis:
            analysis_key[number] = analysis.strip()

    return answer_key, analysis_key


def extract_central_answer_key(text: str) -> tuple[str, dict[int, str], dict[int, str]]:
    lines = text.splitlines()
    cleaned_lines: list[str] = []
    answer_key: dict[int, str] = {}
    analysis_key: dict[int, str] = {}
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        header_match = CENTRAL_ANSWER_HEADER_RE.match(stripped)
        if not header_match:
            cleaned_lines.append(line)
            index += 1
            continue

        header_pairs, header_analyses = parse_central_answer_details(header_match.group(1))
        if header_pairs:
            answer_key.update(header_pairs)
            analysis_key.update(header_analyses)
            index += 1
            while index < len(lines):
                continuation_pairs, continuation_analyses = parse_central_answer_details(lines[index].strip())
                if not continuation_pairs:
                    break
                answer_key.update(continuation_pairs)
                analysis_key.update(continuation_analyses)
                index += 1
            continue

        lookahead_index = index + 1
        lookahead_pairs: dict[int, str] = {}
        lookahead_analyses: dict[int, str] = {}
        while lookahead_index < len(lines):
            next_line = lines[lookahead_index].strip()
            if not next_line:
                lookahead_index += 1
                continue
            next_pairs, next_analyses = parse_central_answer_details(next_line)
            if not next_pairs:
                break
            lookahead_pairs.update(next_pairs)
            lookahead_analyses.update(next_analyses)
            lookahead_index += 1

        if lookahead_pairs:
            answer_key.update(lookahead_pairs)
            analysis_key.update(lookahead_analyses)
            index = lookahead_index
            continue

        cleaned_lines.append(line)
        index += 1

    return "\n".join(cleaned_lines), answer_key, analysis_key


@dataclass
class ParsedQuestion:
    number: int
    stem: str = ""
    options: dict[str, str] = field(default_factory=dict)
    answer: str = ""
    analysis: str = ""
    issues: list[str] = field(default_factory=list)


def validate_single_choice_question(question: ParsedQuestion) -> list[str]:
    issues: list[str] = []

    for label in ("A", "B", "C", "D"):
        if not question.options.get(label):
            issues.append(f"缺少{label}选项")

    if not question.answer:
        issues.append("缺少答案")
    elif question.answer not in question.options:
        issues.append("答案不在已识别选项中")

    if not question.stem:
        issues.append("缺少题干")

    return issues


def sorted_option_labels(options: dict[str, str]) -> list[str]:
    return sorted(
        (label.upper() for label in options),
        key=lambda label: OPTION_LABEL_ORDER.find(label) if label in OPTION_LABEL_ORDER else len(OPTION_LABEL_ORDER),
    )


def normalize_formula_text(value: str, subject: Subject = "general") -> str:
    result = value

    result = re.sub(r"\$([^$]+)\$", r"\1", result)
    result = re.sub(r"\\\((.*?)\\\)", r"\1", result)
    result = re.sub(r"\\\[(.*?)\\\]", r"\1", result, flags=re.S)
    result = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", replace_latex_fraction, result)

    for old_text, new_text in LATEX_REPLACEMENTS.items():
        result = result.replace(old_text, new_text)

    for pattern, replacement in SUPERSCRIPT_MAP.items():
        result = result.replace(pattern, replacement)

    for pattern, replacement in COMPLEX_SUPERSCRIPT_RULES:
        result = pattern.sub(replacement, result)

    result = re.sub(r"_\{([^{}]+)\}", replace_subscript, result)
    result = re.sub(r"_([0-9+-]+)", replace_subscript, result)

    if subject == "chemistry":
        result = result.replace("->", "→").replace("<->", "⇌")
        result = re.sub(r"\((aq|s|l|g)\)", lambda match: f"（{match.group(1)}）", result)

    for old_char, new_char in CHAR_REPLACEMENTS.items():
        result = result.replace(old_char, new_char)

    return result.replace("(", "（").replace(")", "）")


def safe_replace(value: str, subject: Subject = "general") -> str:
    return normalize_formula_text(value, subject)


def normalize_stem(value: str, subject: Subject = "general") -> str:
    stem = value.strip()
    return re.sub(r"((?:\(\s*\)|（\s*）))\s*(?=[①②③④⑤⑥⑦⑧⑨⑩])", r"\1\n", stem)


def normalize_option(value: str, subject: Subject = "general") -> str:
    return value.strip()


def append_stem_line(stem: str, line: str) -> str:
    if not line:
        return stem
    return "\n".join(part for part in [stem, line] if part)


def detect_text_state(text: str) -> Literal["text", "empty", "needs_ocr"]:
    stripped = text.strip()
    if not stripped:
        return "empty"

    chinese_or_latin = len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", stripped))
    if chinese_or_latin < 24:
        return "needs_ocr"

    return "text"


def parse_single_choice_questions(text: str, subject: Subject = "general") -> list[ParsedQuestion]:
    text_without_answer_key, central_answer_key, central_analysis_key = extract_central_answer_key(text)
    questions: list[ParsedQuestion] = []
    current: ParsedQuestion | None = None
    active_field: tuple[str, str | None] | None = None
    pending_analysis = False

    def finish_current() -> None:
        if current is None:
            return

        current.issues = validate_single_choice_question(current)
        questions.append(current)

    for raw_line in split_inline_segments(text_without_answer_key):
        line = raw_line.strip()
        if not line:
            continue

        question_match = QUESTION_NUMBER_RE.match(line)
        if question_match:
            finish_current()
            number_text = question_match.group(1) or question_match.group(2) or str(len(questions) + 1)
            stem = question_match.group(3) or ""
            current = ParsedQuestion(number=int(number_text), stem=normalize_stem(stem, subject))
            active_field = ("stem", None)
            pending_analysis = False
            continue

        if current is None:
            continue

        option_match = OPTION_RE.match(line)
        if option_match:
            label = normalize_option_label(
                first_present(
                    option_match.group(1),
                    option_match.group(2),
                    option_match.group(3),
                    option_match.group(4),
                    option_match.group(5),
                )
            )
            current.options[label] = normalize_option(option_match.group(6), subject)
            active_field = ("option", label)
            pending_analysis = False
            continue

        answer_match = ANSWER_RE.match(line)
        if answer_match:
            current.answer = normalize_option_label(answer_match.group(1))
            trailing = answer_match.group(2).strip()
            if trailing:
                current.analysis = normalize_option(trailing, subject)
                active_field = ("analysis", None)
            else:
                active_field = ("answer", None)
                pending_analysis = True
            continue

        analysis_match = ANALYSIS_RE.match(line)
        if analysis_match:
            current.analysis = normalize_option(analysis_match.group(1), subject)
            active_field = ("analysis", None)
            pending_analysis = False
            continue

        if pending_analysis and current.answer and not current.analysis:
            current.analysis = normalize_option(line, subject)
            active_field = ("analysis", None)
            pending_analysis = False
            continue

        if active_field is None:
            current.stem = append_stem_line(current.stem, normalize_stem(line, subject))
            active_field = ("stem", None)
            continue

        field_name, label = active_field
        cleaned = normalize_option(line, subject)
        if field_name == "option" and label:
            current.options[label] = " ".join(part for part in [current.options.get(label, ""), cleaned] if part)
        elif field_name == "analysis":
            current.analysis = " ".join(part for part in [current.analysis, cleaned] if part)
        else:
            current.stem = append_stem_line(current.stem, normalize_stem(line, subject))

    finish_current()
    for question in questions:
        if not question.answer and question.number in central_answer_key:
            question.answer = central_answer_key[question.number]
        if not question.analysis and question.number in central_analysis_key:
            question.analysis = normalize_option(central_analysis_key[question.number], subject)
        question.issues = validate_single_choice_question(question)
    return questions


def export_kshuati_text(questions: list[ParsedQuestion], subject: Subject = "general") -> str:
    blocks: list[str] = []

    for index, question in enumerate(questions, 1):
        lines = [
            f"{index}.{safe_replace(ANSWER_PLACEHOLDER_RE.sub('', question.stem).strip(), subject)}",
            "()",
        ]

        for label in sorted_option_labels(question.options):
            lines.append(f"{label}.{safe_replace(question.options.get(label, '').strip(), subject)}")

        if question.answer:
            lines.append(f"答案:{question.answer.upper()}")

        if question.analysis:
            lines.append(f"解析:{safe_replace(question.analysis.strip(), subject)}")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)
