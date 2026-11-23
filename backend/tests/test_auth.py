from tests.conftest import PASSWORD, forged_token, user_row


def test_signup_login_and_profile(make, anon):
    a = make()
    me = a.get("/api/v1/users/me")
    assert me.status_code == 200 and me.json()["role"] == "user" and "password_hash" not in me.text
    # একই ইমেইল (বড় হাতের অক্ষরেও) আবার নেওয়া যায় না
    dup = anon.post("/api/v1/auth/signup", json={"email": a.email.upper(), "name": "Dup", "password": PASSWORD})
    assert dup.status_code == 409
    # দুর্বল পাসওয়ার্ড বা ভুল ইমেইল 422
    assert anon.post("/api/v1/auth/signup", json={"email": "x@y.com", "name": "Xy", "password": "short"}).status_code == 422
    assert anon.post("/api/v1/auth/signup", json={"email": "x@y.com", "name": "Xy", "password": "onlyletters"}).status_code == 422
    assert anon.post("/api/v1/auth/signup", json={"email": "not-an-email", "name": "Xy", "password": PASSWORD}).status_code == 422
    # প্রোফাইল বদল
    r = a.patch("/api/v1/users/me", {"name": "New Name", "phone": "01712345678"})
    assert r.status_code == 200 and r.json()["name"] == "New Name"
    assert a.patch("/api/v1/users/me", {"phone": "123"}).status_code == 422


def test_wrong_password_and_unknown_email_look_the_same(make, anon):
    a = make()
    wrong = anon.post("/api/v1/auth/login", json={"email": a.email, "password": "Wrong12345"})
    unknown = anon.post("/api/v1/auth/login", json={"email": "nobody@test.com", "password": "Wrong12345"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_token_rejections(make, anon):
    a = make()
    assert anon.get("/api/v1/users/me").status_code == 401  # token নেই
    assert anon.get("/api/v1/users/me", headers={"Authorization": "Bearer junk"}).status_code == 401  # ভুল token
    # সই বদলে দিলে (ভুল secret) 401
    forged = forged_token(a.id, secret="x" * 40)
    assert anon.get("/api/v1/users/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    # মেয়াদ শেষ হলে 401
    expired = forged_token(a.id, minutes=-1)
    r = anon.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and r.json()["detail"] == "Token expired"
    # payload বদলে সই না মেলালে (tampered) 401
    head, payload, sig = a.token.split(".")
    assert anon.get("/api/v1/users/me", headers={"Authorization": f"Bearer {head}.{payload[:-2]}xx.{sig}"}).status_code == 401


def test_refresh_rotation_reuse_and_logout(make, anon):
    a = make()
    old_cookie = a.client.cookies.get("refresh_token")
    r = a.client.post("/api/v1/auth/refresh")  # cookie দিয়ে নতুন access token
    assert r.status_code == 200 and r.json()["access_token"]
    new_cookie = a.client.cookies.get("refresh_token")
    assert new_cookie != old_cookie  # rotation
    # পুরনো refresh token আবার দিলে (চুরি ধরে নিই) 401, আর session বন্ধ
    anon.cookies.set("refresh_token", old_cookie, path="/api/v1/auth")  # চোরের নিজের কোনো cookie নেই
    assert anon.post("/api/v1/auth/refresh").status_code == 401
    assert a.client.post("/api/v1/auth/refresh").status_code == 401  # আসল ব্যবহারকারীর session-ও বন্ধ হয়েছে


def test_logout_really_invalidates_session(make):
    a = make()
    cookie = a.client.cookies.get("refresh_token")
    assert a.client.post("/api/v1/auth/logout").status_code == 204
    a.client.cookies.set("refresh_token", cookie, path="/api/v1/auth")
    assert a.client.post("/api/v1/auth/refresh").status_code == 401  # সার্ভারে session বাতিল


def test_sessions_list_and_revoke(make):
    a = make()
    second = a.client.post("/api/v1/auth/login", json={"email": a.email, "password": PASSWORD})
    assert second.status_code == 200
    sessions = a.get("/api/v1/auth/sessions").json()
    assert len(sessions) >= 2 and sum(s["current"] for s in sessions) == 1
    other = next(s for s in sessions if not s["current"])
    assert a.delete(f"/api/v1/auth/sessions/{other['id']}").status_code == 204
    assert len(a.get("/api/v1/auth/sessions").json()) == len(sessions) - 1
    # অন্যের session মোছা যায় না
    b = make()
    assert b.delete(f"/api/v1/auth/sessions/{sessions[0]['id']}").status_code == 404


def test_lockout_after_five_failures(make, anon):
    a = make()
    for _ in range(5):
        assert anon.post("/api/v1/auth/login", json={"email": a.email, "password": "Wrong12345"}).status_code == 401
    # এখন সঠিক পাসওয়ার্ড দিলেও লক
    r = anon.post("/api/v1/auth/login", json={"email": a.email, "password": PASSWORD})
    assert r.status_code == 429
    assert user_row(a.id).locked_until is not None


def test_change_password(make, anon):
    a = make()
    other_device = a.client.post("/api/v1/auth/login", json={"email": a.email, "password": PASSWORD})
    assert other_device.status_code == 200
    bad = a.post("/api/v1/users/me/password", {"current_password": "Wrong12345", "new_password": "NewPass123"})
    assert bad.status_code == 400  # ভুল বর্তমান পাসওয়ার্ড
    assert a.post("/api/v1/users/me/password", {"current_password": PASSWORD, "new_password": "weak"}).status_code == 422
    ok = a.post("/api/v1/users/me/password", {"current_password": PASSWORD, "new_password": "NewPass123"})
    assert ok.status_code == 204
    assert anon.post("/api/v1/auth/login", json={"email": a.email, "password": PASSWORD}).status_code == 401
    assert anon.post("/api/v1/auth/login", json={"email": a.email, "password": "NewPass123"}).status_code == 200
