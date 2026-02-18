# tests/test_memberships.py

def test_membership_create_owner_only_201(as_owner, as_tenant):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    u1 = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"}).json()

    # owner adds tenant (user 1)
    res = as_owner.post("/memberships/", json={"user_id": 1, "unit_id": u1["id"], "role": "tenant"})
    assert res.status_code == 201, res.text

    # tenant cannot create memberships
    res = as_tenant.post("/memberships/", json={"user_id": 2, "unit_id": u1["id"], "role": "manager"})
    assert res.status_code == 403


def test_membership_create_duplicate_409(as_owner):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    u1 = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"}).json()

    assert as_owner.post("/memberships/", json={"user_id": 1, "unit_id": u1["id"], "role": "tenant"}).status_code == 201
    res = as_owner.post("/memberships/", json={"user_id": 1, "unit_id": u1["id"], "role": "tenant"})
    assert res.status_code == 409


def test_membership_create_common_400(as_owner):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()

    # owner's memberships in building include COMMON unit membership
    res = as_owner.get(f"/memberships/?building_id={b['id']}")
    assert res.status_code == 200, res.text
    common_unit_id = res.json()[0]["unit_id"]

    # try to assign tenant (user 1) to COMMON -> should 400
    res = as_owner.post("/memberships/", json={"user_id": 1, "unit_id": common_unit_id, "role": "tenant"})
    assert res.status_code == 400, res.text


def test_membership_delete_cannot_remove_only_owner_403(as_owner):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    res = as_owner.get(f"/memberships/?building_id={b['id']}")
    assert res.status_code == 200
    owner_membership_id = res.json()[0]["id"]

    res = as_owner.delete(f"/memberships/{owner_membership_id}")
    assert res.status_code == 403, res.text


def test_get_my_memberships_in_building_200(as_owner):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    res = as_owner.get(f"/memberships/?building_id={b['id']}")
    assert res.status_code == 200
    assert len(res.json()) >= 1
