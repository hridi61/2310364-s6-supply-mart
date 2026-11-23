from tests.conftest import product_body


def test_health_seed_and_public_reads(anon):
    assert anon.get("/api/health").json() == {"status": "ok"}
    assert len(anon.get("/api/v1/categories").json()) == 8
    r = anon.get("/api/v1/products?limit=5")
    assert r.status_code == 200 and len(r.json()) == 5 and int(r.headers["x-total-count"]) >= 18
    assert anon.get("/api/v1/products/99999").status_code == 404
    assert anon.get("/api/v1/products?limit=0").status_code == 422


def test_filter_and_sort(anon):
    r = anon.get("/api/v1/products?category=dal&sort=price_asc")
    prices = [p["price"] for p in r.json()]
    assert r.status_code == 200 and prices and prices == sorted(prices)
    assert all(p["category_slug"] == "dal" for p in r.json())


def test_crud_flow_and_validation(make):
    a = make()
    r = a.post("/api/v1/products", product_body())
    assert r.status_code == 201 and r.json()["owner_id"] == a.id
    pid = r.json()["id"]
    assert a.patch(f"/api/v1/products/{pid}", {"price": 75}).json()["price"] == 75
    assert a.post("/api/v1/products", product_body(price=0)).status_code == 422
    assert a.post("/api/v1/products", product_body(category_id=999)).status_code == 422
    assert a.patch(f"/api/v1/products/{pid}", {"name_bn": None}).status_code == 422
    assert a.delete(f"/api/v1/products/{pid}").status_code == 204
