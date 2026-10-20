from __future__ import annotations

import json

import pytest
from langchain_core.documents import Document

from docculus.transform import (
    format_documents,
    format_documents_as_json,
    format_documents_as_markdown,
    format_documents_as_xml,
)

######################################
#     Tests for format_documents     #
######################################


def test_format_documents_default_is_xml() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    assert format_documents(documents) == format_documents_as_xml(documents)


def test_format_documents_output_format_xml() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    assert format_documents(documents, output_format="xml") == format_documents_as_xml(documents)


def test_format_documents_output_format_markdown() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    assert format_documents(documents, output_format="markdown") == format_documents_as_markdown(
        documents
    )


def test_format_documents_output_format_json() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    assert format_documents(documents, output_format="json") == format_documents_as_json(documents)


def test_format_documents_output_format_markdown_with_metadata() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
    ]
    assert format_documents(
        documents, include_metadata=True, output_format="markdown"
    ) == format_documents_as_markdown(documents, include_metadata=True)


def test_format_documents_output_format_xml_with_metadata() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
    ]
    assert format_documents(
        documents, include_metadata=True, output_format="xml"
    ) == format_documents_as_xml(documents, include_metadata=True)


def test_format_documents_output_format_json_with_metadata() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
    ]
    assert format_documents(
        documents, include_metadata=True, output_format="json"
    ) == format_documents_as_json(documents, include_metadata=True)


def test_format_documents_empty() -> None:
    assert format_documents([]) == ""
    assert format_documents([], output_format="markdown") == ""
    assert format_documents([], output_format="json") == "[]"


def test_format_documents_invalid_output_format_raises() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    with pytest.raises(ValueError, match="Unknown format: bogus"):
        format_documents(documents, output_format="bogus")


######################################################
#     Tests for format_documents_as_markdown         #
######################################################


def test_format_documents_as_markdown_empty() -> None:
    assert format_documents_as_markdown([]) == ""


def test_format_documents_as_markdown_single_document() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    assert format_documents_as_markdown(documents) == ("## Document 1\n\nThe cat sat on the mat.")


def test_format_documents_as_markdown_multiple_documents() -> None:
    documents = [
        Document(page_content="The cat sat on the mat."),
        Document(page_content="The dog chased the ball."),
    ]
    assert format_documents_as_markdown(documents) == (
        "## Document 1\n\nThe cat sat on the mat.\n\n## Document 2\n\nThe dog chased the ball."
    )


def test_format_documents_as_markdown_without_metadata_ignores_metadata() -> None:
    documents = [
        Document(page_content="The cat sat on the mat.", metadata={"source": "story.txt"}),
    ]
    assert format_documents_as_markdown(documents, include_metadata=False) == (
        "## Document 1\n\nThe cat sat on the mat."
    )


def test_format_documents_as_markdown_with_metadata_single_document() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
    ]
    assert format_documents_as_markdown(documents, include_metadata=True) == (
        "## Document 1\n\n- author: Alice\n- source: story.txt\n\nThe cat sat on the mat."
    )


def test_format_documents_as_markdown_with_metadata_multiple_documents() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
        Document(
            page_content="The dog chased the ball.",
            metadata={"source": "story.txt", "author": "Bob"},
        ),
    ]
    assert format_documents_as_markdown(documents, include_metadata=True) == (
        "## Document 1\n"
        "\n"
        "- author: Alice\n"
        "- source: story.txt\n"
        "\n"
        "The cat sat on the mat.\n"
        "\n"
        "## Document 2\n"
        "\n"
        "- author: Bob\n"
        "- source: story.txt\n"
        "\n"
        "The dog chased the ball."
    )


def test_format_documents_as_markdown_with_metadata_sorted_by_key() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"zebra": "z", "apple": "a", "mango": "m"},
        ),
    ]
    assert format_documents_as_markdown(documents, include_metadata=True) == (
        "## Document 1\n\n- apple: a\n- mango: m\n- zebra: z\n\nThe cat sat on the mat."
    )


def test_format_documents_as_markdown_with_metadata_true_but_empty_metadata() -> None:
    documents = [Document(page_content="The cat sat on the mat.", metadata={})]
    assert format_documents_as_markdown(documents, include_metadata=True) == (
        "## Document 1\n\nThe cat sat on the mat."
    )


######################################################
#     Tests for format_documents_as_xml              #
######################################################


def test_format_documents_as_xml_empty() -> None:
    assert format_documents_as_xml([]) == ""


def test_format_documents_as_xml_single_document() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    assert format_documents_as_xml(documents) == (
        '<document id="1">\nThe cat sat on the mat.\n</document>'
    )


def test_format_documents_as_xml_multiple_documents() -> None:
    documents = [
        Document(page_content="The cat sat on the mat."),
        Document(page_content="The dog chased the ball."),
    ]
    assert format_documents_as_xml(documents) == (
        '<document id="1">\n'
        "The cat sat on the mat.\n"
        "</document>\n"
        "\n"
        '<document id="2">\n'
        "The dog chased the ball.\n"
        "</document>"
    )


def test_format_documents_as_xml_without_metadata_ignores_metadata() -> None:
    documents = [
        Document(page_content="The cat sat on the mat.", metadata={"source": "story.txt"}),
    ]
    assert format_documents_as_xml(documents, include_metadata=False) == (
        '<document id="1">\nThe cat sat on the mat.\n</document>'
    )


def test_format_documents_as_xml_with_metadata_single_document() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
    ]
    assert format_documents_as_xml(documents, include_metadata=True) == (
        '<document id="1">\n'
        "author: Alice\n"
        "source: story.txt\n"
        "\n"
        "The cat sat on the mat.\n"
        "</document>"
    )


def test_format_documents_as_xml_with_metadata_multiple_documents() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
        Document(
            page_content="The dog chased the ball.",
            metadata={"source": "story.txt", "author": "Bob"},
        ),
    ]
    assert format_documents_as_xml(documents, include_metadata=True) == (
        '<document id="1">\n'
        "author: Alice\n"
        "source: story.txt\n"
        "\n"
        "The cat sat on the mat.\n"
        "</document>\n"
        "\n"
        '<document id="2">\n'
        "author: Bob\n"
        "source: story.txt\n"
        "\n"
        "The dog chased the ball.\n"
        "</document>"
    )


def test_format_documents_as_xml_with_metadata_sorted_by_key() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"zebra": "z", "apple": "a", "mango": "m"},
        ),
    ]
    assert format_documents_as_xml(documents, include_metadata=True) == (
        '<document id="1">\napple: a\nmango: m\nzebra: z\n\nThe cat sat on the mat.\n</document>'
    )


def test_format_documents_as_xml_with_metadata_true_but_empty_metadata() -> None:
    documents = [Document(page_content="The cat sat on the mat.", metadata={})]
    assert format_documents_as_xml(documents, include_metadata=True) == (
        '<document id="1">\nThe cat sat on the mat.\n</document>'
    )


######################################################
#     Tests for format_documents_as_json             #
######################################################


def test_format_documents_as_json_empty() -> None:
    assert format_documents_as_json([]) == "[]"


def test_format_documents_as_json_single_document() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    result = format_documents_as_json(documents)
    assert json.loads(result) == [{"id": 1, "content": "The cat sat on the mat."}]


def test_format_documents_as_json_multiple_documents() -> None:
    documents = [
        Document(page_content="The cat sat on the mat."),
        Document(page_content="The dog chased the ball."),
    ]
    result = format_documents_as_json(documents)
    assert json.loads(result) == [
        {"id": 1, "content": "The cat sat on the mat."},
        {"id": 2, "content": "The dog chased the ball."},
    ]


def test_format_documents_as_json_without_metadata_ignores_metadata() -> None:
    documents = [
        Document(page_content="The cat sat on the mat.", metadata={"source": "story.txt"}),
    ]
    result = format_documents_as_json(documents, include_metadata=False)
    assert json.loads(result) == [{"id": 1, "content": "The cat sat on the mat."}]


def test_format_documents_as_json_with_metadata_single_document() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
    ]
    result = format_documents_as_json(documents, include_metadata=True)
    assert json.loads(result) == [
        {
            "id": 1,
            "metadata": {"author": "Alice", "source": "story.txt"},
            "content": "The cat sat on the mat.",
        }
    ]


def test_format_documents_as_json_with_metadata_multiple_documents() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
        Document(
            page_content="The dog chased the ball.",
            metadata={"source": "story.txt", "author": "Bob"},
        ),
    ]
    result = format_documents_as_json(documents, include_metadata=True)
    assert json.loads(result) == [
        {
            "id": 1,
            "metadata": {"author": "Alice", "source": "story.txt"},
            "content": "The cat sat on the mat.",
        },
        {
            "id": 2,
            "metadata": {"author": "Bob", "source": "story.txt"},
            "content": "The dog chased the ball.",
        },
    ]


def test_format_documents_as_json_with_metadata_sorted_by_key() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"zebra": "z", "apple": "a", "mango": "m"},
        ),
    ]
    result = format_documents_as_json(documents, include_metadata=True)
    parsed = json.loads(result)
    assert list(parsed[0]["metadata"].keys()) == ["apple", "mango", "zebra"]


def test_format_documents_as_json_with_metadata_true_but_empty_metadata() -> None:
    documents = [Document(page_content="The cat sat on the mat.", metadata={})]
    result = format_documents_as_json(documents, include_metadata=True)
    assert json.loads(result) == [{"id": 1, "content": "The cat sat on the mat."}]


def test_format_documents_as_json_is_valid_json() -> None:
    documents = [
        Document(
            page_content='Line one.\nLine "two" with quotes.',
            metadata={"source": "story.txt"},
        ),
    ]
    result = format_documents_as_json(documents, include_metadata=True)
    # Should not raise, and should round-trip content exactly.
    parsed = json.loads(result)
    assert parsed[0]["content"] == 'Line one.\nLine "two" with quotes.'


def test_format_documents_as_json_single_document_exact_string() -> None:
    documents = [Document(page_content="The cat sat on the mat.")]
    assert format_documents_as_json(documents) == (
        '[\n  {\n    "id": 1,\n    "content": "The cat sat on the mat."\n  }\n]'
    )


def test_format_documents_as_json_multiple_documents_exact_string() -> None:
    documents = [
        Document(page_content="The cat sat on the mat."),
        Document(page_content="The dog chased the ball."),
    ]
    assert format_documents_as_json(documents) == (
        "[\n"
        "  {\n"
        '    "id": 1,\n'
        '    "content": "The cat sat on the mat."\n'
        "  },\n"
        "  {\n"
        '    "id": 2,\n'
        '    "content": "The dog chased the ball."\n'
        "  }\n"
        "]"
    )


def test_format_documents_as_json_with_metadata_single_document_exact_string() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
    ]
    assert format_documents_as_json(documents, include_metadata=True) == (
        "[\n"
        "  {\n"
        '    "id": 1,\n'
        '    "metadata": {\n'
        '      "author": "Alice",\n'
        '      "source": "story.txt"\n'
        "    },\n"
        '    "content": "The cat sat on the mat."\n'
        "  }\n"
        "]"
    )


def test_format_documents_as_json_with_metadata_multiple_documents_exact_string() -> None:
    documents = [
        Document(
            page_content="The cat sat on the mat.",
            metadata={"source": "story.txt", "author": "Alice"},
        ),
        Document(
            page_content="The dog chased the ball.",
            metadata={"source": "story.txt", "author": "Bob"},
        ),
    ]
    assert format_documents_as_json(documents, include_metadata=True) == (
        "[\n"
        "  {\n"
        '    "id": 1,\n'
        '    "metadata": {\n'
        '      "author": "Alice",\n'
        '      "source": "story.txt"\n'
        "    },\n"
        '    "content": "The cat sat on the mat."\n'
        "  },\n"
        "  {\n"
        '    "id": 2,\n'
        '    "metadata": {\n'
        '      "author": "Bob",\n'
        '      "source": "story.txt"\n'
        "    },\n"
        '    "content": "The dog chased the ball."\n'
        "  }\n"
        "]"
    )


def test_format_documents_use_doc_ids_xml() -> None:
    docs = [Document(id="a", page_content="A"), Document(page_content="B")]
    assert format_documents_as_xml(docs, use_doc_ids=True) == (
        '<document id="a">\nA\n</document>\n\n<document id="2">\nB\n</document>'
    )


def test_format_documents_use_doc_ids_markdown() -> None:
    docs = [Document(id="a", page_content="A")]
    assert format_documents_as_markdown(docs, use_doc_ids=True) == "## Document a\n\nA"


def test_format_documents_use_doc_ids_json() -> None:
    docs = [Document(id="a", page_content="A"), Document(page_content="B")]
    result = json.loads(format_documents_as_json(docs, use_doc_ids=True))
    assert [entry["id"] for entry in result] == ["a", "2"]


def test_format_documents_use_doc_ids_dispatcher() -> None:
    docs = [Document(id="a", page_content="A")]
    assert 'id="a"' in format_documents(docs, use_doc_ids=True)


def test_format_documents_as_xml_escapes_content_metadata_and_ids() -> None:
    docs = [Document(id='x"><b', page_content="</document> & <b>", metadata={"k<": "v&"})]
    result = format_documents_as_xml(docs, include_metadata=True, use_doc_ids=True)
    assert "</document> &" not in result
    assert "&lt;/document&gt; &amp; &lt;b&gt;" in result
    assert "k&lt;: v&amp;" in result
    assert result.count("</document>") == 1


def test_format_documents_nested_metadata_rendered_as_json() -> None:
    docs = [Document(page_content="A", metadata={"tags": ["a", "b"], "n": {"x": 1}})]
    result = format_documents_as_markdown(docs, include_metadata=True)
    assert '- n: {"x": 1}' in result
    assert '- tags: ["a", "b"]' in result


def test_format_documents_as_json_indent_and_ensure_ascii() -> None:
    docs = [Document(page_content="café")]
    assert "café" in format_documents_as_json(docs)
    assert "\\u00e9" in format_documents_as_json(docs, ensure_ascii=True)
    assert "\n" not in format_documents_as_json(docs, indent=None)


def test_format_documents_accepts_generator() -> None:
    docs = (Document(page_content=c) for c in "AB")
    assert (
        format_documents(docs, output_format="markdown")
        == "## Document 1\n\nA\n\n## Document 2\n\nB"
    )
