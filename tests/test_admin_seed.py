def test_seed_endpoint(client):
    resp = client.post("/admin/seed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["users_created"] > 0
    assert data["products_created"] > 0
