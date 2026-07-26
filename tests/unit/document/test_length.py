from __future__ import annotations

from langchain_core.documents import Document

from docculus.document import (
    get_length,
    get_lengths,
    get_lengths_with_ids,
    get_longest_document,
    get_shortest_document,
)

################################
#     Tests for get_length     #
################################


def test_get_length_basic() -> None:
    assert get_length(Document(page_content="hello")) == 5


def test_get_length_empty() -> None:
    assert get_length(Document(page_content="")) == 0


def test_get_length_none_content() -> None:
    doc = Document(page_content="x")
    doc.page_content = None
    assert get_length(doc) == 0


#################################
#     Tests for get_lengths     #
#################################


def test_get_lengths_empty() -> None:
    assert get_lengths([]) == []


def test_get_lengths_basic() -> None:
    docs = [
        Document(id="a", page_content="hello"),
        Document(id="b", page_content="hello world"),
    ]
    assert get_lengths(docs) == [5, 11]


def test_get_lengths_none_content() -> None:
    doc = Document(id="a", page_content="x")
    doc.page_content = None
    assert get_lengths([doc]) == [0]


def test_get_lengths_generator() -> None:
    def gen() -> object:
        yield Document(id="a", page_content="ab")
        yield Document(id="b", page_content="")

    assert get_lengths(gen()) == [2, 0]


####################################
#     Tests for get_lengths_with_ids     #
####################################


def test_get_lengths_with_ids_empty() -> None:
    assert get_lengths_with_ids([]) == []


def test_get_lengths_with_ids_basic() -> None:
    docs = [
        Document(id="a", page_content="hello"),
        Document(id="b", page_content="hello world"),
    ]
    assert get_lengths_with_ids(docs) == [("a", 5), ("b", 11)]


def test_get_lengths_with_ids_none_content() -> None:
    doc = Document(id="a", page_content="x")
    doc.page_content = None
    assert get_lengths_with_ids([doc]) == [("a", 0)]


def test_get_lengths_with_ids_generator() -> None:
    def gen() -> object:
        yield Document(id="a", page_content="ab")
        yield Document(id="b", page_content="")

    assert get_lengths_with_ids(gen()) == [("a", 2), ("b", 0)]


def test_get_lengths_with_ids_sort_true() -> None:
    docs = [
        Document(id="a", page_content="hello world"),
        Document(id="b", page_content=""),
        Document(id="c", page_content="hi"),
    ]
    assert get_lengths_with_ids(docs, sort=True) == [("b", 0), ("c", 2), ("a", 11)]


def test_get_lengths_with_ids_sort_false_default() -> None:
    docs = [
        Document(id="a", page_content="hello world"),
        Document(id="b", page_content="hi"),
    ]
    assert get_lengths_with_ids(docs) == [("a", 11), ("b", 2)]


def test_get_lengths_with_ids_sort_stable_ties() -> None:
    docs = [
        Document(id="a", page_content="ab"),
        Document(id="b", page_content="cd"),
    ]
    assert get_lengths_with_ids(docs, sort=True) == [("a", 2), ("b", 2)]


###########################################
#     Tests for get_shortest_document     #
###########################################


def test_get_shortest_empty_iterable() -> None:
    assert get_shortest_document([]) is None


def test_get_shortest_basic() -> None:
    docs = [
        Document(id="a", page_content="hello world"),
        Document(id="b", page_content="hi"),
        Document(id="c", page_content="hello"),
    ]
    assert get_shortest_document(docs).id == "b"


def test_get_shortest_ties_first_occurrence() -> None:
    docs = [
        Document(id="a", page_content="ab"),
        Document(id="b", page_content="cd"),
    ]
    assert get_shortest_document(docs).id == "a"


def test_get_shortest_generator() -> None:
    def gen() -> object:
        yield Document(id="a", page_content="hello")
        yield Document(id="b", page_content="hi")

    assert get_shortest_document(gen()).id == "b"


def test_get_shortest_ignore_empty_false_default() -> None:
    docs = [
        Document(id="a", page_content="hello"),
        Document(id="b", page_content=""),
        Document(id="c", page_content="  "),
    ]
    assert get_shortest_document(docs).id == "b"


def test_get_shortest_ignore_empty_true() -> None:
    docs = [
        Document(id="a", page_content="hello world"),
        Document(id="b", page_content=""),
        Document(id="c", page_content="  "),
        Document(id="d", page_content="hi"),
    ]
    assert get_shortest_document(docs, ignore_empty=True).id == "c"


def test_get_shortest_ignore_empty_all_ignored() -> None:
    docs = [
        Document(id="a", page_content=""),
    ]
    assert get_shortest_document(docs, ignore_empty=True) is None


def test_get_shortest_ignore_empty_treat_whitespace_as_empty_true() -> None:
    docs = [
        Document(id="a", page_content="hello world"),
        Document(id="b", page_content=""),
        Document(id="c", page_content="  "),
        Document(id="d", page_content="hi"),
    ]
    assert get_shortest_document(docs, ignore_empty=True, treat_whitespace_as_empty=True).id == "d"


def test_get_shortest_ignore_empty_treat_whitespace_as_empty_all_ignored() -> None:
    docs = [
        Document(id="a", page_content=""),
        Document(id="b", page_content="   "),
    ]
    assert get_shortest_document(docs, ignore_empty=True, treat_whitespace_as_empty=True) is None


def test_get_shortest_treat_whitespace_as_empty_no_effect_without_ignore_empty() -> None:
    docs = [
        Document(id="a", page_content=" "),
        Document(id="b", page_content="hi"),
    ]
    assert get_shortest_document(docs, treat_whitespace_as_empty=True).id == "a"


##########################################
#     Tests for get_longest_document     #
##########################################


def test_get_longest_empty_iterable() -> None:
    assert get_longest_document([]) is None


def test_get_longest_basic() -> None:
    docs = [
        Document(id="a", page_content="hi"),
        Document(id="b", page_content="hello world"),
        Document(id="c", page_content="hello"),
    ]
    assert get_longest_document(docs).id == "b"


def test_get_longest_ties_first_occurrence() -> None:
    docs = [
        Document(id="a", page_content="ab"),
        Document(id="b", page_content="cd"),
    ]
    assert get_longest_document(docs).id == "a"


def test_get_longest_generator() -> None:
    def gen() -> object:
        yield Document(id="a", page_content="hi")
        yield Document(id="b", page_content="hello")

    assert get_longest_document(gen()).id == "b"


def test_get_longest_ignore_empty_false_default() -> None:
    docs = [
        Document(id="a", page_content="hello"),
        Document(id="b", page_content=""),
    ]
    assert get_longest_document(docs).id == "a"


def test_get_longest_ignore_empty_true_all_ignored() -> None:
    docs = [
        Document(id="a", page_content=""),
    ]
    assert get_longest_document(docs, ignore_empty=True) is None


def test_get_longest_ignore_empty_treat_whitespace_as_empty_all_ignored() -> None:
    docs = [
        Document(id="a", page_content=""),
        Document(id="b", page_content="   "),
    ]
    assert get_longest_document(docs, ignore_empty=True, treat_whitespace_as_empty=True) is None


def test_get_longest_ignore_empty_treat_whitespace_as_empty_false() -> None:
    docs = [
        Document(id="a", page_content=""),
        Document(id="b", page_content="   "),
    ]
    assert get_longest_document(docs, ignore_empty=True).id == "b"
