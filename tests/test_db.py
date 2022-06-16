import pytest
from japarr.db import JaparrDB

def test_db_drama():
    db = JaparrDB(":memory:?cache=shared")
    db.add_episode("Test_drama", "http://test-drama.com", 2, 1, 0)
    db.add_episode("Test_drama", "http://test-drama.com", 2, 2, 0)
    episodes = db.get_drama("Test_drama")
    db.add_movie("Test_movie", "http://test-drama.com")
    movie = db.get_movie("Test_movie")
    assert len(episodes) == 2
    assert episodes[0][4] == 1
    assert movie[1] == "Test_movie"