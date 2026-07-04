from backend.app.kshuati_converter import (
    export_kshuati_text,
    normalize_formula_text,
    parse_single_choice_questions,
    safe_replace,
)


def test_safe_replace_keeps_kshuati_placeholders_safe():
    assert safe_replace("|A+B| = (A+B)^(-1)、A^2") == "｜A+B｜ = （A+B）⁻¹，A²"


def test_parse_single_choice_questions_with_common_number_and_option_styles():
    text = """
第1题：中国特色社会主义最本质的特征是（ ）
A、中国共产党领导
B 人民民主专政
C.共同富裕
D）依法治国
答案：A
解析：中国共产党领导是中国特色社会主义最本质的特征。

2、下列说法正确的是
A.甲
B.乙
C.丙
D.丁
参考答案:B
"""

    questions = parse_single_choice_questions(text)

    assert len(questions) == 2
    assert questions[0].stem == "中国特色社会主义最本质的特征是（ ）"
    assert questions[0].options["A"] == "中国共产党领导"
    assert questions[0].answer == "A"
    assert questions[0].analysis == "中国共产党领导是中国特色社会主义最本质的特征。"
    assert questions[1].answer == "B"


def test_parse_single_choice_questions_splits_inline_options_answer_and_analysis():
    text = "1.下列说法正确的是（ ） A.选项甲 B.选项乙 C.选项丙 D.选项丁 答案:B 解析:乙正确"

    questions = parse_single_choice_questions(text)

    assert len(questions) == 1
    assert questions[0].stem == "下列说法正确的是（ ）"
    assert questions[0].options == {
        "A": "选项甲",
        "B": "选项乙",
        "C": "选项丙",
        "D": "选项丁",
    }
    assert questions[0].answer == "B"
    assert questions[0].analysis == "乙正确"
    assert questions[0].issues == []


def test_parse_single_choice_questions_preserves_multiline_stem_for_review():
    text = """
1.马克思、恩格斯指出，下列说法正确的是（ ）
①“大工业”是推动世界历史进步的根本动力
②开放合作、互利共赢是世界历史发展的必然要求
③当今推动经济全球化的主要力量依然是美国等西方国家
④马克思恩格斯世界历史理论揭示了经济全球化的发展趋势
A.①③
B.①④
C.②③
D.②④
答案:D
"""

    questions = parse_single_choice_questions(text)

    assert questions[0].stem == (
        "马克思、恩格斯指出，下列说法正确的是（ ）\n"
        "①“大工业”是推动世界历史进步的根本动力\n"
        "②开放合作、互利共赢是世界历史发展的必然要求\n"
        "③当今推动经济全球化的主要力量依然是美国等西方国家\n"
        "④马克思恩格斯世界历史理论揭示了经济全球化的发展趋势"
    )
    assert questions[0].options == {"A": "①③", "B": "①④", "C": "②③", "D": "②④"}
    assert questions[0].answer == "D"


def test_parse_single_choice_questions_breaks_circled_items_after_placeholder():
    text = "1.马克思、恩格斯指出，下列说法正确的是（ ）①“大工业”是推动世界历史进步的根本动力②开放合作是必然要求 A.① B.② C.①② D.③ 答案:C"

    questions = parse_single_choice_questions(text)

    assert questions[0].stem.startswith("马克思、恩格斯指出，下列说法正确的是（ ）\n①")


def test_parse_single_choice_questions_keeps_inline_math_option_content():
    text = "1.函数 y=x^2 的图像是（ ） A.直线 B.抛物线 C.双曲线 D.圆 答案:B"

    questions = parse_single_choice_questions(text, subject="math")

    assert questions[0].stem == "函数 y=x^2 的图像是（ ）"
    assert questions[0].options["B"] == "抛物线"
    assert questions[0].answer == "B"


def test_parse_single_choice_questions_accepts_fullwidth_option_labels():
    text = "1.下列正确的是（ ） Ａ．选项甲 Ｂ．选项乙 Ｃ．选项丙 Ｄ．选项丁 答案：Ｂ"

    questions = parse_single_choice_questions(text)

    assert len(questions) == 1
    assert questions[0].options == {
        "A": "选项甲",
        "B": "选项乙",
        "C": "选项丙",
        "D": "选项丁",
    }
    assert questions[0].answer == "B"
    assert questions[0].issues == []


def test_parse_single_choice_questions_splits_compact_inline_options():
    text = "1.下列正确的是（ ）A.选项甲B.选项乙C.选项丙D.选项丁答案:B"

    questions = parse_single_choice_questions(text)

    assert len(questions) == 1
    assert questions[0].stem == "下列正确的是（ ）"
    assert questions[0].options == {
        "A": "选项甲",
        "B": "选项乙",
        "C": "选项丙",
        "D": "选项丁",
    }
    assert questions[0].answer == "B"
    assert questions[0].issues == []


def test_parse_single_choice_questions_accepts_parenthesized_options():
    text = """
1.下列正确的是（ ）
(A)选项甲
(B)选项乙
(C)选项丙
(D)选项丁
答案:B
"""

    questions = parse_single_choice_questions(text)

    assert questions[0].options == {
        "A": "选项甲",
        "B": "选项乙",
        "C": "选项丙",
        "D": "选项丁",
    }
    assert questions[0].answer == "B"
    assert questions[0].issues == []


def test_parse_single_choice_questions_accepts_fullwidth_parenthesized_inline_options():
    text = "1.下列正确的是（ ） （A）选项甲 （B）选项乙 （C）选项丙 （D）选项丁 答案:B"

    questions = parse_single_choice_questions(text)

    assert questions[0].options["A"] == "选项甲"
    assert questions[0].options["D"] == "选项丁"
    assert questions[0].answer == "B"


def test_parse_single_choice_questions_accepts_bracketed_web_bank_markers():
    text = "1.下列正确的是（ ） 【A】甲 【B】乙 【C】丙 【D】丁 【答案】B 【解析】乙正确"

    questions = parse_single_choice_questions(text)

    assert questions[0].stem == "下列正确的是（ ）"
    assert questions[0].options == {
        "A": "甲",
        "B": "乙",
        "C": "丙",
        "D": "丁",
    }
    assert questions[0].answer == "B"
    assert questions[0].analysis == "乙正确"
    assert questions[0].issues == []


def test_parse_single_choice_questions_accepts_square_bracket_web_bank_markers():
    text = "1.下列正确的是（ ） [A]甲 [B]乙 [C]丙 [D]丁 [答案]B [解析]乙正确"

    questions = parse_single_choice_questions(text)

    assert questions[0].options == {
        "A": "甲",
        "B": "乙",
        "C": "丙",
        "D": "丁",
    }
    assert questions[0].answer == "B"
    assert questions[0].analysis == "乙正确"
    assert questions[0].issues == []


def test_parse_single_choice_questions_does_not_split_english_words_as_options():
    text = "1.Which ABC statement is correct? A.Alpha B.Beta C.Gamma D.Delta Answer:B"

    questions = parse_single_choice_questions(text)

    assert questions[0].stem == "Which ABC statement is correct?"
    assert questions[0].options["A"] == "Alpha"
    assert questions[0].answer == "B"


def test_parse_single_choice_questions_accepts_english_answer_headers():
    text = """
1.Which statement is correct?
A.Alpha
B.Beta
C.Gamma
D.Delta
Correct Answer: D
"""

    questions = parse_single_choice_questions(text)

    assert questions[0].answer == "D"
    assert questions[0].issues == []


def test_parse_single_choice_questions_applies_central_answer_key():
    text = """
1.第一题 A.甲 B.乙 C.丙 D.丁
2.第二题 A.甲 B.乙 C.丙 D.丁
答案：1.B 2.C
"""

    questions = parse_single_choice_questions(text)

    assert len(questions) == 2
    assert questions[0].answer == "B"
    assert questions[1].answer == "C"
    assert questions[0].issues == []
    assert questions[1].issues == []


def test_parse_single_choice_questions_accepts_fullwidth_central_answers():
    text = """
1.第一题 A.甲 B.乙 C.丙 D.丁
2.第二题 A.甲 B.乙 C.丙 D.丁
答案：1.Ｂ 2.Ｃ
"""

    questions = parse_single_choice_questions(text)

    assert [question.answer for question in questions] == ["B", "C"]


def test_parse_single_choice_questions_accepts_english_central_answer_key():
    text = """
1.First question A.Alpha B.Beta C.Gamma D.Delta
2.Second question A.Alpha B.Beta C.Gamma D.Delta
Answer Key: 1.B 2.C
"""

    questions = parse_single_choice_questions(text)

    assert [question.answer for question in questions] == ["B", "C"]


def test_parse_single_choice_questions_applies_multiline_central_answer_key():
    text = """
1.第一题 A.甲 B.乙 C.丙 D.丁
2.第二题 A.甲 B.乙 C.丙 D.丁
参考答案
1、A
2、D
"""

    questions = parse_single_choice_questions(text)

    assert len(questions) == 2
    assert [question.answer for question in questions] == ["A", "D"]


def test_parse_single_choice_questions_applies_central_answer_analysis_key():
    text = """
1.第一题 A.甲 B.乙 C.丙 D.丁
2.第二题 A.甲 B.乙 C.丙 D.丁
答案及解析：1.B 解析：第一题选乙。 2.C 解析：第二题选丙。
"""

    questions = parse_single_choice_questions(text)

    assert len(questions) == 2
    assert questions[0].answer == "B"
    assert questions[0].analysis == "第一题选乙。"
    assert questions[1].answer == "C"
    assert questions[1].analysis == "第二题选丙。"


def test_parse_single_choice_questions_applies_multiline_central_answer_analysis_key():
    text = """
1.第一题 A.甲 B.乙 C.丙 D.丁
2.第二题 A.甲 B.乙 C.丙 D.丁
参考答案及解析
1、A 解析：第一题解析。
2、D 解析：第二题解析。
"""

    questions = parse_single_choice_questions(text)

    assert [question.answer for question in questions] == ["A", "D"]
    assert [question.analysis for question in questions] == ["第一题解析。", "第二题解析。"]


def test_export_kshuati_text_uses_required_placeholder_line():
    questions = parse_single_choice_questions(
        """
1.设A，B为n阶方阵，则下列式子一定正确的是()
A.|A+B| = |A| + |B|
B.|AB| = |BA|
C.AB = BA
D.(A+B)^(-1) = A^(-1) + B^(-1)
答案:B
解析:由行列式乘法性质可知。
"""
    )

    output = export_kshuati_text(questions)

    assert "1.设A，B为n阶方阵，则下列式子一定正确的是\n()\n" in output
    assert "A.｜A+B｜ = ｜A｜ + ｜B｜" in output
    assert "D.（A+B）⁻¹ = A⁻¹ + B⁻¹" in output
    assert "答案:B" in output


def test_missing_answer_and_option_are_reported():
    questions = parse_single_choice_questions(
        """
1.只有三个选项的题
A.一
B.二
C.三
"""
    )

    assert "缺少D选项" in questions[0].issues
    assert "缺少答案" in questions[0].issues


def test_math_latex_and_subscript_are_normalized_for_export():
    text = normalize_formula_text(r"$\frac{a}{b} \leq x_2 \times \alpha$", subject="math")

    assert text == "a/b ≤ x₂ × α"


def test_chemistry_formula_and_reaction_are_normalized_for_export():
    text = normalize_formula_text("Ca(OH)_2 + CO_2 -> CaCO_3(s)", subject="chemistry")

    assert text == "Ca（OH）₂ + CO₂ → CaCO₃（s）"
