"""প্রশিক্ষকের জন্য demo অ্যাকাউন্ট ও নমুনা ডেটা।

চালানো:   DEMO_PASSWORD="...." python -m app.seed_demo
পাসওয়ার্ড কোডে বা README-তে থাকে না, শুধু environment variable থেকে আসে।
আগে থেকে থাকা অ্যাকাউন্ট বদলায় না (বারবার চালালেও সমস্যা নেই)।
"""
import os
import sys

from sqlmodel import Session, select

from app.auth.models import User
from app.auth.schemas import check_password
from app.catalog.models import Category, Product
from app.database import DATABASE_URL, engine, init_db
from app.groups.models import Group, GroupMember
from app.security import hash_password

USERS = [
    ("admin1@supplymart.test", "Admin One", "admin"),
    ("admin2@supplymart.test", "Admin Two", "admin"),
    ("rahim@supplymart.test", "Rahim Uddin", "user"),
    ("karim@supplymart.test", "Karim Hossain", "user"),
    ("salma@supplymart.test", "Salma Akter", "user"),
]


def main() -> None:
    password = os.getenv("DEMO_PASSWORD", "")
    try:
        check_password(password)
    except ValueError as exc:
        sys.exit(f"DEMO_PASSWORD ঠিক নেই: {exc}")

    # পাসওয়ার্ড hash-এ PEPPER মেশে। Vercel-এর PEPPER-এর সাথে না মিললে demo লগইন কাজ করবে না
    if not DATABASE_URL.startswith("sqlite") and not os.getenv("PEPPER"):
        sys.exit("Supabase-এ seed করতে PEPPER দিতে হবে, Vercel-এ যে মান বসিয়েছেন হুবহু সেটাই।")

    init_db()
    with Session(engine) as session:
        users: dict[str, User] = {}
        for email, name, role in USERS:
            user = session.exec(select(User).where(User.email == email)).first()
            if user is None:
                user = User(email=email, name=name, role=role, password_hash=hash_password(password))
                session.add(user)
                session.commit()
                session.refresh(user)
                print(f"created {role}: {email}")
            users[email] = user

        rahim, karim, salma = (users[e] for e in ("rahim@supplymart.test", "karim@supplymart.test", "salma@supplymart.test"))
        group = session.exec(select(Group).where(Group.name == "Mirpur Fresh Mart")).first()
        if group is None:
            group = Group(name="Mirpur Fresh Mart", description="মিরপুরের তাজা মুদির দোকান (demo গ্রুপ)", owner_id=rahim.id)
            session.add(group)
            session.commit()
            session.refresh(group)
            # মিশ্র অনুমতি: Karim সব বদলাতে পারে, Salma শুধু স্টক
            session.add(GroupMember(group_id=group.id, user_id=karim.id, permissions="create,update"))
            session.add(GroupMember(group_id=group.id, user_id=salma.id, permissions="stock"))
            session.commit()
            print("created group: Mirpur Fresh Mart")

            cats = {c.slug: c.id for c in session.exec(select(Category)).all()}
            samples = [
                (rahim, group, "দেশি মুরগি", "mangsho", "kg", 420, 25),
                (rahim, group, "তাজা পালংশাক", "sobji", "kg", 40, 60),
                (karim, group, "রুই মাছ", "mach", "kg", 340, 30),
                (rahim, None, "ঘরে ভাজা মুড়ি", "chal", "kg", 110, 40),
                (karim, None, "খেজুরের গুড়", "moshla", "kg", 280, 15),
                (salma, None, "ঘরের তৈরি আচার", "moshla", "piece", 180, 20),
            ]
            for owner, grp, name, slug, unit, price, stock in samples:
                session.add(Product(name_bn=name, category_id=cats[slug], unit=unit, price=price, stock=stock,
                                    owner_id=owner.id, group_id=grp.id if grp else None))
            session.commit()
            print("created sample products")
    print("Done.")


if __name__ == "__main__":
    main()
