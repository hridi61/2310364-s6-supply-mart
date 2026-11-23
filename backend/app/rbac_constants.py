"""অনুমতির নামগুলো (constant) ও কোন role-এ কোনটা আছে, শুধু ডেটা — কোনো import নেই।"""


class P:
    """গ্লোবাল অনুমতি (role-ভিত্তিক)"""

    PROFILE = "profile:manage"
    PRODUCT_WRITE = "product:write"  # নিজের (বা গ্রুপের) পণ্য যোগ/বদল/মোছা, মালিকানা আলাদা করে দেখা হয়
    GROUP_CREATE = "group:create"
    SESSION_MANAGE = "session:manage"

    ADMIN_STATS = "admin:stats"
    ADMIN_USERS_READ = "admin:users:read"
    ADMIN_USERS_BAN = "admin:users:ban"
    ADMIN_USERS_ROLE = "admin:users:role"
    ADMIN_CONTENT = "admin:content"
    ADMIN_ACTIVITY = "admin:activity"
    ADMIN_EXPORT = "admin:export"


USER_PERMISSIONS = {P.PROFILE, P.PRODUCT_WRITE, P.GROUP_CREATE, P.SESSION_MANAGE}
ADMIN_ONLY = {
    P.ADMIN_STATS, P.ADMIN_USERS_READ, P.ADMIN_USERS_BAN, P.ADMIN_USERS_ROLE,
    P.ADMIN_CONTENT, P.ADMIN_ACTIVITY, P.ADMIN_EXPORT,
}
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "user": set(USER_PERMISSIONS),
    "admin": USER_PERMISSIONS | ADMIN_ONLY,
}

# গ্রুপের ভেতরের অনুমতি (সদস্য ভেদে আলাদা)
GROUP_PERMS = ("create", "update", "stock")
