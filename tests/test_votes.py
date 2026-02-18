# tests/test_votes.py

def setup_for_votes(as_owner, as_manager, as_tenant):
    b = as_owner.post("/buildings/", json={"name": "B1", "address": "A1"}).json()
    u1 = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "101"}).json()
    u2 = as_owner.post("/units/", json={"building_id": b["id"], "unit_number": "102"}).json()

    # owner adds manager(user2) + tenant(user1) to unit101
    assert as_owner.post("/memberships/", json={"user_id": 2, "unit_id": u1["id"], "role": "manager"}).status_code == 201
    assert as_owner.post("/memberships/", json={"user_id": 1, "unit_id": u1["id"], "role": "tenant"}).status_code == 201

    req_resp = as_tenant.post("/maintenance-requests/", json={"unit_id": u1["id"], "title": "Leak", "description": "Fix"})
    assert req_resp.status_code == 201, req_resp.text
    req = req_resp.json()

    return b, u1, u2, req


def test_votes_lifecycle_201_409_201_404(as_owner, as_manager, as_tenant):
    b, u1, u2, req = setup_for_votes(as_owner, as_manager, as_tenant)

    res = as_tenant.post("/votes/", json={"maintenance_request_id": req["id"], "dir": 1})
    assert res.status_code == 201, res.text

    res = as_tenant.post("/votes/", json={"maintenance_request_id": req["id"], "dir": 1})
    assert res.status_code == 409, res.text

    res = as_tenant.post("/votes/", json={"maintenance_request_id": req["id"], "dir": 0})
    assert res.status_code == 201, res.text

    res = as_tenant.post("/votes/", json={"maintenance_request_id": req["id"], "dir": 0})
    assert res.status_code == 404, res.text


def test_votes_owner_cannot_vote_403(as_owner, as_manager, as_tenant):
    b, u1, u2, req = setup_for_votes(as_owner, as_manager, as_tenant)

    res = as_owner.post("/votes/", json={"maintenance_request_id": req["id"], "dir": 1})
    assert res.status_code == 403, res.text


def test_votes_tenant_other_unit_403(as_owner, as_manager, as_tenant):
    b, u1, u2, req = setup_for_votes(as_owner, as_manager, as_tenant)

    # give manager membership to unit102 so manager can create a request there
    assert as_owner.post("/memberships/", json={"user_id": 2, "unit_id": u2["id"], "role": "manager"}).status_code == 201

    req2_resp = as_manager.post("/maintenance-requests/", json={"unit_id": u2["id"], "title": "Other", "description": "X"})
    assert req2_resp.status_code == 201, req2_resp.text
    req2 = req2_resp.json()

    # tenant is not a member of unit102 => cannot vote
    res = as_tenant.post("/votes/", json={"maintenance_request_id": req2["id"], "dir": 1})
    assert res.status_code == 403, res.text


def test_votes_manager_can_vote_any_request_in_building_201(as_owner, as_manager, as_tenant):
    b, u1, u2, req = setup_for_votes(as_owner, as_manager, as_tenant)

    # manager creates request in unit102 (needs membership there)
    assert as_owner.post("/memberships/", json={"user_id": 2, "unit_id": u2["id"], "role": "manager"}).status_code == 201

    req2_resp = as_manager.post("/maintenance-requests/", json={"unit_id": u2["id"], "title": "Other", "description": "X"})
    assert req2_resp.status_code == 201, req2_resp.text
    req2 = req2_resp.json()

    # manager can vote across building
    res = as_manager.post("/votes/", json={"maintenance_request_id": req2["id"], "dir": 1})
    assert res.status_code == 201, res.text
