def make(client, **changes):
    data = {"name_bn": "মিনিকেট চাল", "category_id": 1, "unit": "kg", "price": 72, "stock": 10}
    data.update(changes)
    return client.post("/api/v1/products", json=data)


def test_create_product(client):
    res = make(client)
    assert res.status_code == 201
    body = res.json()
    assert body["name_bn"] == "মিনিকেট চাল"
    assert body["category_slug"] == "chal"
    assert body["is_active"] is True


def test_list_products_with_total(client):
    make(client)
    make(client, name_bn="নাজিরশাইল চাল")
    res = client.get("/api/v1/products")
    assert res.status_code == 200
    assert res.headers["X-Total-Count"] == "2"
    assert len(res.json()) == 2


def test_search_products(client):
    make(client)
    make(client, name_bn="নাজিরশাইল চাল")
    res = client.get("/api/v1/products", params={"q": "নাজির"})
    assert res.headers["X-Total-Count"] == "1"


def test_get_one_product(client):
    product_id = make(client).json()["id"]
    res = client.get(f"/api/v1/products/{product_id}")
    assert res.status_code == 200
    assert res.json()["id"] == product_id


def test_get_missing_product_returns_404(client):
    assert client.get("/api/v1/products/999").status_code == 404


def test_patch_changes_only_sent_fields(client):
    product_id = make(client).json()["id"]
    res = client.patch(f"/api/v1/products/{product_id}", json={"price": 80})
    assert res.status_code == 200
    body = res.json()
    assert body["price"] == 80
    assert body["name_bn"] == "মিনিকেট চাল"


def test_patch_missing_product_returns_404(client):
    assert client.patch("/api/v1/products/999", json={"price": 80}).status_code == 404


def test_delete_product(client):
    product_id = make(client).json()["id"]
    assert client.delete(f"/api/v1/products/{product_id}").status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").status_code == 404


def test_delete_missing_product_returns_404(client):
    assert client.delete("/api/v1/products/999").status_code == 404


def test_validation_errors_return_422(client):
    assert make(client, price=0).status_code == 422
    assert make(client, name_bn="   ").status_code == 422
    assert make(client, unit="box").status_code == 422
    assert make(client, category_id=999).status_code == 422