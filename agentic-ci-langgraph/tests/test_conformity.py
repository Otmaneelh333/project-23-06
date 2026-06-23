"""Tests unitaires des règles de conformité des réponses."""

import pytest

from app.graph import validate_answer_node


def test_valid_answer_is_conform():
    result = validate_answer_node(
        {"answer": "Morocco is located in North Africa, near Europe."}
    )

    assert result["is_conform"] is True
    assert result["conformity_errors"] == []


@pytest.mark.parametrize(
    ("answer", "expected_error"),
    [
        ("", "La réponse est vide."),
        ("Trop court", "La réponse doit contenir au moins 20 caractères."),
        ("Cette réponse contient None, ce qui est invalide.", "La réponse contient la valeur interdite 'None'."),
        ("Cette réponse contient NaN, ce qui est invalide.", "La réponse contient la valeur interdite 'NaN'."),
    ],
    ids=["empty", "too_short", "contains_none", "contains_nan"],
)
def test_invalid_answers_are_not_conform(answer, expected_error):
    result = validate_answer_node({"answer": answer})

    assert result["is_conform"] is False
    assert expected_error in result["conformity_errors"]
