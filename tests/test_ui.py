from pathlib import Path
import json

import pytest
from streamlit.testing.v1 import AppTest
from reachsignal import portable as io

APP=Path(__file__).resolve().parents[1]/"app.py"


def page(a,i):
    a.sidebar.radio[0].set_value(a.sidebar.radio[0].options[i]).run()
    assert not a.exception


@pytest.mark.parametrize("i",range(7))
def test_all_pages(i):
    a=AppTest.from_file(str(APP),default_timeout=30).run()
    page(a,i)
    assert not a.error


def test_ai_import_review_and_candidate_selection():
    a=AppTest.from_file(str(APP),default_timeout=30).run()
    d=a.session_state["reach:project"]["data"]
    page(a,1)
    a.radio(key="reach:input_mode").set_value("Use your AI").run()
    a.text_area(key="reach:ai_json").set_value(json.dumps(d))
    a.button(key="reach:import").click().run()
    page(a,3)
    assert not a.metric
    page(a,2)
    a.text_input[0].set_value("Reviewer")
    next(x for x in a.text_area if x.label=="What did you check?").set_value("Checked coordinates, demand and model parameters.")
    a.checkbox[0].check()
    next(x for x in a.button if x.label=="Record review").click().run()
    assert io.reviewed(a.session_state["reach:project"])
    page(a,3)
    baseline=a.metric[0].value
    a.selectbox(key="reach:scenario").set_value("C1").run()
    assert not a.exception and not a.error
    assert a.metric[0].value!=baseline
    page(a,2)
    next(x for x in a.button if x.label=="Save edited inputs").click().run()
    assert not a.exception and not a.error
    assert not io.reviewed(a.session_state["reach:project"])


def test_blank_case_can_be_edited_and_saved_without_fake_results():
    a=AppTest.from_file(str(APP),default_timeout=30).run()
    page(a,1)
    a.radio(key="reach:input_mode").set_value("Use your AI").run()
    next(x for x in a.text_area if x.label=="Your business, question and scope").set_value("Our actual trade area")
    next(x for x in a.button if x.label=="Start blank case").click().run()
    for i in [2,3,4,5]:
        page(a,i)
        assert not a.error
