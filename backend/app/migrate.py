"""পুরনো `product` টেবিলে নতুন কলাম যোগ করে (create_all শুধু নতুন টেবিল বানায়, কলাম বদলায় না)।"""
import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("supply_mart")


def ensure_columns(engine: Engine) -> None:
    insp = inspect(engine)
    if "product" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("product")}
    wanted = {
        "owner_id": "ALTER TABLE product ADD COLUMN owner_id INTEGER REFERENCES app_user(id)",
        "group_id": "ALTER TABLE product ADD COLUMN group_id INTEGER REFERENCES shop_group(id)",
    }
    for column, statement in wanted.items():
        if column in existing:
            continue
        try:
            with engine.begin() as conn:
                conn.execute(text(statement))
            logger.info("Added product.%s", column)
        except Exception:  # একই সময়ে আরেকটা process যোগ করে ফেললে এখানে আসে
            logger.warning("Could not add product.%s (maybe already added)", column)
