"""The tool that summarises real student sessions. The rows here are made-up toy rows used
only to check the arithmetic and the matching of course names; they are not study data."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ml", "experiments", "student_evaluation"))

from analyse_sessions import analyse, describe, normalise, same_programme  # noqa: E402

TITLES = ["Bachelor of Science in Software Engineering", "Bachelor of Pharmacy (BPharm)", "Bachelor of Laws (LLB)"]


def row(**kw):
    base = {"id": "S", "device": "emulator", "placed_course": "", "shown_1": "", "shown_2": "", "shown_3": "",
            "finished_without_help": "yes", "minutes": "5", "rating_easy": "4", "rating_reasons": "4",
            "rating_consider": "4", "rating_recommend": "4", "comment": ""}
    base.update(kw)
    return base


def test_everyday_course_names_match_the_catalogue_titles():
    assert same_programme("BSc Software Engineering", "Bachelor of Science in Software Engineering")
    assert same_programme("Pharmacy", "Bachelor of Pharmacy (BPharm)")
    assert not same_programme("Law", "Bachelor of Pharmacy (BPharm)")
    assert not same_programme("", "Law")


def test_normalising_drops_filler_words():
    assert normalise("Bachelor of Science in Software Engineering") == "software engineering"


def test_the_hit_rate_counts_only_students_placed_in_a_covered_programme():
    rows = [
        row(placed_course="Pharmacy", shown_1="Bachelor of Laws (LLB)", shown_3="Bachelor of Pharmacy (BPharm)"),
        row(placed_course="Software Engineering", shown_1="Bachelor of Laws (LLB)"),
        row(placed_course="Nursing"),
    ]
    result = analyse(rows, TITLES)
    assert result["placed_in_covered_programme"] == 2
    assert result["hit_in_top_three"] == 1
    assert result["not_covered"] == 1


def test_completion_time_and_ratings_come_from_the_rows():
    rows = [row(minutes="4", rating_easy="5"), row(minutes="8", rating_easy="3", finished_without_help="no")]
    result = analyse(rows, TITLES)
    assert result["finished_without_help"] == 1
    assert result["median_minutes"] == 6.0
    assert result["ratings"]["rating_easy"] == {"n": 2, "mean": 4.0, "agree": 1}


def test_a_blank_rating_is_left_out_not_counted_as_zero():
    result = analyse([row(rating_easy=""), row(rating_easy="4")], TITLES)
    assert result["ratings"]["rating_easy"]["n"] == 1


def test_the_description_states_the_counts_it_was_given():
    text = describe(analyse([row(placed_course="Law", shown_2="Bachelor of Laws (LLB)")], TITLES))
    assert "1 students took part" in text and "1 of these 1 (100%)" in text
