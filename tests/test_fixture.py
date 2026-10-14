def test_fixture_loads(conn):
    assert conn.execute("SELECT count(*) FROM associations").fetchone() == (11,)
