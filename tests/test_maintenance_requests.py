# tests/test_maintenance_requests.py

def setup_building_units_memberships(as_owner, db, as_manager=None, as_tenant=None):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    u1 = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"}).json()
    u2 = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "102"}).json()

    # owner adds manager (user 2) + tenant (user 1) to unit101
    assert as_owner.post("/memberships/", json={"user_id": 2, "unit_id": u1["id"], "role": "manager"}).status_code == 201
    assert as_owner.post("/memberships/", json={"user_id": 1, "unit_id": u1["id"], "role": "tenant"}).status_code == 201
    return b, u1, u2


def test_maint_post_unit_201(as_owner, as_tenant, db):
    b, u1, u2 = setup_building_units_memberships(as_owner, db)

    res = as_tenant.post("/maintenance-requests/", json={"unit_id": u1["id"], "title": "Leak", "description": "Fix"})
    assert res.status_code == 201, res.text
    assert res.json()["unit_id"] == u1["id"]


def test_maint_post_other_unit_403(as_owner, as_tenant, db):
    b, u1, u2 = setup_building_units_memberships(as_owner, db)

    # tenant is NOT a member of unit102
    res = as_tenant.post("/maintenance-requests/", json={"unit_id": u2["id"], "title": "No", "description": "No"})
    assert res.status_code == 403, res.text


def test_maint_list_any_building_member_200(as_owner, as_manager, db):
    b, u1, u2 = setup_building_units_memberships(as_owner, db)

    # manager belongs to building because membership in unit101 exists
    # create request as manager (allowed because manager is member of unit101)
    res_create = as_manager.post("/maintenance-requests/", json={"unit_id": u1["id"], "title": "Leak", "description": "Fix"})
    assert res_create.status_code == 201, res_create.text

    res = as_manager.get(f"/maintenance-requests/?building_id={b['id']}")
    assert res.status_code == 200, res.text
    assert len(res.json()) == 1
    assert "maintenance" in res.json()[0]
    assert "votes" in res.json()[0]


def test_maint_get_by_id_requires_building_membership_200_for_manager(as_owner, as_manager, db):
    b, u1, u2 = setup_building_units_memberships(as_owner, db)

    req = as_manager.post("/maintenance-requests/", json={"unit_id": u1["id"], "title": "Leak", "description": "Fix"})
    assert req.status_code == 201, req.text
    req_id = req.json()["id"]

    res = as_manager.get(f"/maintenance-requests/{req_id}")
    assert res.status_code == 200, res.text


def test_maint_patch_status_manager_or_owner_200(as_owner, as_manager, as_tenant, db):
    b, u1, u2 = setup_building_units_memberships(as_owner, db)

    # create request as tenant (tenant is member of unit101)
    req = as_tenant.post("/maintenance-requests/", json={"unit_id": u1["id"], "title": "Leak", "description": "Fix"})
    assert req.status_code == 201, req.text
    req_id = req.json()["id"]

    # tenant cannot patch
    res = as_tenant.patch(f"/maintenance-requests/{req_id}", json={"status": "resolved"})
    assert res.status_code == 403, res.text

    # manager can patch
    res = as_manager.patch(f"/maintenance-requests/{req_id}", json={"status": "resolved"})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "resolved"
