from sqlmodel import Session, select

from app.catalog.models import Category, Product

CATEGORIES = [
    ("chal", "চাল", "🍚"),
    ("dal", "ডাল", "🫘"),
    ("tel", "তেল", "🛢️"),
    ("sobji", "সবজি", "🥬"),
    ("mach", "মাছ", "🐟"),
    ("mangsho", "মাংস", "🍗"),
    ("dim-dudh", "ডিম-দুধ", "🥚"),
    ("moshla", "মসলা", "🌶️"),
]

# (ক্যাটাগরির slug, নাম, একক, দাম, স্টক)
PRODUCTS = [
    ("chal", "মিনিকেট চাল", "kg", 72, 200),
    ("chal", "নাজিরশাইল চাল", "kg", 78, 150),
    ("chal", "স্বর্ণা চাল", "kg", 58, 300),
    ("dal", "মসুর ডাল", "kg", 135, 90),
    ("dal", "মুগ ডাল", "kg", 150, 60),
    ("dal", "ছোলা", "kg", 120, 80),
    ("tel", "সয়াবিন তেল", "litre", 190, 120),
    ("tel", "সরিষার তেল", "litre", 265, 40),
    ("sobji", "আলু", "kg", 35, 500),
    ("sobji", "পেঁয়াজ", "kg", 85, 400),
    ("sobji", "বেগুন", "kg", 88, 120),
    ("mach", "ইলিশ মাছ", "kg", 1800, 25),
    ("mach", "রুই মাছ", "kg", 320, 50),
    ("mangsho", "ব্রয়লার মুরগি", "kg", 210, 70),
    ("mangsho", "গরুর মাংস", "kg", 780, 35),
    ("dim-dudh", "ডিম (ফার্ম)", "dozen", 135, 200),
    ("dim-dudh", "তরল দুধ", "litre", 100, 80),
    ("moshla", "হলুদ গুঁড়া", "kg", 380, 30),
]


def seed_if_empty(session: Session) -> None:
    """ডেটাবেস একদম খালি থাকলে ক্যাটাগরি ও নমুনা পণ্য বসায়।"""
    if session.exec(select(Category)).first() is not None:
        return

    for slug, name_bn, icon in CATEGORIES:
        session.add(Category(slug=slug, name_bn=name_bn, icon=icon))
    session.commit()

    by_slug = {c.slug: c for c in session.exec(select(Category)).all()}
    for slug, name_bn, unit, price, stock in PRODUCTS:
        session.add(
            Product(category_id=by_slug[slug].id, name_bn=name_bn, unit=unit, price=price, stock=stock)
        )
    session.commit()