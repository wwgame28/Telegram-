from app.agent import WorkAgent


def test_extract_nested_payload():
    payload = {'data': {'jobs': [{'id': '1'}, {'id': '2'}]}}
    assert len(WorkAgent._extract_list(payload, ('jobs','data','results','items'))) == 2
