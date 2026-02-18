# tests/test_buildings.py

def test_building_create_201_creates_common_and_owner_membership(as_owner):
    res = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"})
    assert res.status_code == 201, res.text
    b = res.json()
    assert b["id"] == 1

    res = as_owner.get("/buildings/")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_building_create_duplicate_409(as_owner):
    assert as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).status_code == 201
    res = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"})
    assert res.status_code == 409


def test_building_get_requires_membership_404(as_owner, as_tenant):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()

    # tenant has NO membership in this building -> should 404 (your route uses join scoping)
    res = as_tenant.get(f"/buildings/{b['id']}")
    assert res.status_code == 404
