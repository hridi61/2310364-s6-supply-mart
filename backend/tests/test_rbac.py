from tests.conftest import PASSWORD, product_body


def test_admin_endpoints_need_admin_role(make, anon):
    user, admin = make(), make("admin")
    assert anon.get("/api/v1/admin/stats").status_code == 401
    for url in ("/api/v1/admin/stats", "/api/v1/admin/users", "/api/v1/admin/activity", "/api/v1/admin/export/users"):
        assert user.get(url).status_code == 403, url
        assert admin.get(url).status_code == 200, url


def test_product_writes_need_login_and_ownership(make, anon):
    a, b = make(), make()
    assert anon.post("/api/v1/products", json=product_body()).status_code == 401
    pid = a.post("/api/v1/products", product_body()).json()["id"]
    assert b.patch(f"/api/v1/products/{pid}", {"price": 99}).status_code == 403  # অন্যের পণ্য
    assert b.delete(f"/api/v1/products/{pid}").status_code == 403
    assert a.patch(f"/api/v1/products/{pid}", {"price": 75}).json()["price"] == 75
    # পাবলিক পড়া চলে, আর মালিক can_edit পায়, অন্যজন পায় না
    assert anon.get(f"/api/v1/products/{pid}").json()["can_edit"] is False
    assert a.get(f"/api/v1/products/{pid}").json()["can_edit"] is True
    assert b.get(f"/api/v1/products/{pid}").json()["can_edit"] is False
    # "আমার পণ্য" শুধু নিজেরটা
    assert [p["id"] for p in a.get("/api/v1/products/mine").json()] == [pid]
    assert b.get("/api/v1/products/mine").json() == []
    assert a.delete(f"/api/v1/products/{pid}").status_code == 204
    assert a.delete(f"/api/v1/products/{pid}").status_code == 404


def test_seeded_platform_products_cannot_be_edited_by_users(make):
    a = make()
    assert a.patch("/api/v1/products/1", {"price": 1}).status_code == 403


def test_group_permissions(make):
    owner, editor, stocker, stranger = make(), make(), make(), make()
    g = owner.post("/api/v1/groups", {"name": "Test Shop"}).json()
    gid = g["id"]
    # সদস্য যোগ (শুধু owner)
    assert editor.post(f"/api/v1/groups/{gid}/members", {"email": stocker.email, "permissions": ["stock"]}).status_code == 404  # বাইরের লোক
    assert owner.post(f"/api/v1/groups/{gid}/members", {"email": editor.email, "permissions": ["create", "update"]}).status_code == 201
    assert owner.post(f"/api/v1/groups/{gid}/members", {"email": stocker.email, "permissions": ["stock"]}).status_code == 201
    assert owner.post(f"/api/v1/groups/{gid}/members", {"email": stocker.email, "permissions": []}).status_code == 409
    assert owner.post(f"/api/v1/groups/{gid}/members", {"email": "x@test.com", "permissions": ["fly"]}).status_code == 422

    # create অনুমতি: editor পারে, stocker পারে না, stranger পারে না
    pid = editor.post("/api/v1/products", product_body(group_id=gid)).json()["id"]
    assert stocker.post("/api/v1/products", product_body(group_id=gid)).status_code == 403
    assert stranger.post("/api/v1/products", product_body(group_id=gid)).status_code == 403

    flags = stocker.get(f"/api/v1/products/{pid}").json()
    assert (flags["can_edit"], flags["can_stock"], flags["can_delete"]) == (False, True, False)
    # stocker শুধু স্টক বদলাতে পারে
    assert stocker.patch(f"/api/v1/products/{pid}", {"stock": 99}).json()["stock"] == 99
    assert stocker.patch(f"/api/v1/products/{pid}", {"price": 1}).status_code == 403
    assert stocker.patch(f"/api/v1/products/{pid}", {"name_bn": "নতুন নাম", "stock": 1}).status_code == 403
    # editor সব বদলাতে পারে, কিন্তু মুছতে পারে না
    assert editor.patch(f"/api/v1/products/{pid}", {"price": 88}).status_code == 200
    # editor নিজেই পণ্যটার মালিক, তাই মুছতে পারে; অন্যের বানানো পণ্য নয়
    own_pid = owner.post("/api/v1/products", product_body(group_id=gid)).json()["id"]
    assert editor.patch(f"/api/v1/products/{own_pid}", {"price": 70}).status_code == 200
    assert editor.delete(f"/api/v1/products/{own_pid}").status_code == 403
    assert stocker.delete(f"/api/v1/products/{own_pid}").status_code == 403
    assert owner.delete(f"/api/v1/products/{pid}").status_code == 204  # গ্রুপ owner যে কোনো গ্রুপ-পণ্য মুছতে পারে

    # rename / member manage / delete: শুধু owner
    assert editor.patch(f"/api/v1/groups/{gid}", {"name": "Hacked"}).status_code == 403
    assert editor.delete(f"/api/v1/groups/{gid}/members/{stocker.id}").status_code == 403
    assert editor.post(f"/api/v1/groups/{gid}/members", {"email": stranger.email, "permissions": []}).status_code == 403
    assert editor.delete(f"/api/v1/groups/{gid}").status_code == 403
    assert owner.patch(f"/api/v1/groups/{gid}", {"name": "Renamed"}).json()["name"] == "Renamed"
    assert owner.patch(f"/api/v1/groups/{gid}/members/{stocker.id}", {"permissions": ["create"]}).status_code == 200
    # বাইরের লোক গ্রুপ দেখতেই পায় না
    assert stranger.get(f"/api/v1/groups/{gid}").status_code == 404
    assert owner.delete(f"/api/v1/groups/{gid}").status_code == 204


def test_admin_safety_rules(make):
    admin1, admin2, user = make("admin"), make("admin"), make()
    # নিজের role বদলানো যায় না, অন্য অ্যাডমিনকে ban করা যায় না
    assert admin1.patch(f"/api/v1/admin/users/{admin1.id}/role", {"role": "user"}).status_code == 403
    assert admin1.post(f"/api/v1/admin/users/{admin2.id}/ban", {"reason": "test reason"}).status_code == 403
    assert admin1.post(f"/api/v1/admin/users/{admin1.id}/ban", {"reason": "test reason"}).status_code == 403
    # ব্যবহারকারীর role বদল
    assert admin1.patch(f"/api/v1/admin/users/{user.id}/role", {"role": "admin"}).json()["role"] == "admin"
    assert user.get("/api/v1/admin/stats").status_code == 200  # DB-র role সাথে সাথে কার্যকর
    assert admin1.patch(f"/api/v1/admin/users/{user.id}/role", {"role": "user"}).json()["role"] == "user"
    assert user.get("/api/v1/admin/stats").status_code == 403


def test_banned_user_is_rejected_on_next_request(make, anon):
    admin, victim = make("admin"), make()
    assert victim.get("/api/v1/users/me").status_code == 200
    assert admin.post(f"/api/v1/admin/users/{victim.id}/ban", {"reason": "spamming"}).status_code == 200
    assert victim.get("/api/v1/users/me").status_code == 403  # একই token, পরের request-ই বন্ধ
    assert victim.client.post("/api/v1/auth/refresh").status_code == 401  # session-ও বাতিল
    login = anon.post("/api/v1/auth/login", json={"email": victim.email, "password": PASSWORD})
    assert login.status_code == 403 and "spamming" in login.json()["detail"]
    assert admin.post(f"/api/v1/admin/users/{victim.id}/unban").status_code == 200
    assert victim.login().status_code == 200


def test_bulk_ban_skips_admins(make):
    admin, other_admin, u1, u2 = make("admin"), make("admin"), make(), make()
    r = admin.post("/api/v1/admin/users/bulk", {"action": "ban", "ids": [u1.id, u2.id, other_admin.id], "reason": "bulk test"})
    assert r.status_code == 200
    body = r.json()
    assert sorted(body["done"]) == sorted([u1.id, u2.id]) and body["skipped"][0]["id"] == other_admin.id
    assert u1.get("/api/v1/users/me").status_code == 403
    assert admin.post("/api/v1/admin/users/bulk", {"action": "unban", "ids": [u1.id, u2.id]}).json()["done"]
    assert u1.get("/api/v1/users/me").status_code == 200


def test_admin_users_filters_detail_and_moderation(make):
    admin, user = make("admin"), make()
    pid = user.post("/api/v1/products", product_body(name_bn="মডারেশন পণ্য")).json()["id"]
    r = admin.get("/api/v1/admin/users", params={"q": user.email, "role": "user", "status": "active"})
    assert r.status_code == 200 and [u["id"] for u in r.json()] == [user.id] and r.headers["x-total-count"] == "1"
    detail = admin.get(f"/api/v1/admin/users/{user.id}").json()
    assert detail["user"]["email"] == user.email and detail["products"][0]["id"] == pid
    assert any(a["action"] == "login" for a in detail["activity"])
    assert admin.get("/api/v1/admin/users/999999").status_code == 404
    listing = admin.get("/api/v1/admin/products", params={"owner_id": user.id}).json()
    assert [p["id"] for p in listing] == [pid]
    assert admin.post("/api/v1/admin/products/bulk-delete", {"ids": [pid]}).json() == {"deleted": 1}
    assert user.get(f"/api/v1/products/{pid}").status_code == 404
    revoked = admin.post(f"/api/v1/admin/users/{user.id}/revoke-sessions").json()["revoked"]
    assert revoked >= 1 and user.client.post("/api/v1/auth/refresh").status_code == 401


def test_activity_log_security_and_csv_export(make, anon):
    admin, user = make("admin"), make()
    anon.post("/api/v1/auth/login", json={"email": user.email, "password": "Wrong12345"})
    log = admin.get("/api/v1/admin/activity", params={"action": "login_failed", "q": user.email}).json()
    assert log and log[0]["action"] == "login_failed" and log[0]["ip"] and log[0]["email"] == user.email
    sec = admin.get("/api/v1/admin/security").json()
    assert any(row["email"] == user.email for row in sec["by_account"]) and sec["by_ip"]
    csv_resp = admin.get("/api/v1/admin/export/users", params={"q": user.email})
    assert csv_resp.status_code == 200 and csv_resp.headers["content-type"].startswith("text/csv")
    assert user.email in csv_resp.text and "password" not in csv_resp.text.lower()
    exports = admin.get("/api/v1/admin/activity", params={"action": "export"}).json()
    assert exports and "users csv" in exports[0]["detail"]  # export-ও log হয়
    assert admin.get("/api/v1/admin/stats").json()["users"] >= 2


def test_csv_formula_injection_is_neutralised():
    from app.admin.service import to_csv
    out = to_csv(["a"], [["=1+1"], ["+cmd"], ["safe"]])
    assert "'=1+1" in out and "'+cmd" in out and "safe" in out
