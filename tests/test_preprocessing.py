import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.load_to_db import clean_body


def test_clean_body():
    html = '<p>Hello <a href="#">click here</a> world</p>'
    result = clean_body(html)
    assert '<a' not in result
    assert "Hello" in result
    assert 'world' in result

