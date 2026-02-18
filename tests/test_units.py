# tests/test_units.py

def test_unit_create_owner_only_201(as_owner, as_tenant):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()

    res = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"})
    assert res.status_code == 201, res.text

    res = as_tenant.post("/units/", json={"building_id": b["id"], "unit_number": "102"})
    assert res.status_code == 403


def test_unit_create_common_409(as_owner):
    # COMMON already exists because building creation created it
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    res = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "COMMON"})
    assert res.status_code == 409


def test_unit_list_requires_building_membership_403(as_owner, as_tenant):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"})

    # tenant has no membership in building
    res = as_tenant.get(f"/units/?building_id={b['id']}")
    assert res.status_code == 403


def test_unit_list_excludes_common(as_owner, as_manager):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    u1 = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"}).json()

    # owner adds manager (user 2) to unit101 => manager belongs to building
    assert as_owner.post("/memberships/", json={"user_id": 2, "unit_id": u1["id"], "role": "manager"}).status_code == 201

    as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "102"})

    res = as_manager.get(f"/units/?building_id={b['id']}")
    assert res.status_code == 200, res.text
    nums = [u["unit_number"] for u in res.json()]
    assert "COMMON" not in nums
    assert nums == ["101", "102"]


def test_unit_get_by_id_requires_unit_membership_403(as_owner, as_tenant):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    unit = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"}).json()

    # tenant has no membership in unit
    res = as_tenant.get(f"/units/{unit['id']}")
    assert res.status_code == 403
