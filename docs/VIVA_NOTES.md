# Viva notes (২৬ নভেম্বর): নিজের কোড নিজের ভাষায় বোঝানোর জন্য

> সব উত্তরের আগে নিজে কোডটা একবার খুলে পড়ুন। নিচে "কোন ফাইলে" লেখা আছে, সেটা খুলে লাইনগুলো মিলিয়ে নিন।
> শুধু মুখস্থ করলে হবে না, স্যার যেকোনো লাইন দেখিয়ে "এটা সরালে কী হবে" জিজ্ঞেস করবেন।

## ১. JWT প্রবাহ (সবচেয়ে বেশি প্রশ্ন আসবে)

**Token কোথায় তৈরি হয়?** `backend/app/security.py` → `create_access_token()`
- payload: `sub` (user id), `role`, `iat`, `exp` (এখন + ১৫ মিনিট), `jti` (আলাদা id)
- `HS256` দিয়ে `JWT_SECRET` (environment variable) দিয়ে সই করা

**কোথায় যাচাই হয়?** `security.py` → `decode_access_token()` ও `auth/dependencies.py` → `get_current_user()`
1. `Authorization: Bearer ...` header থেকে token নেয়
2. সই ও মেয়াদ দেখে। ভুল বা মেয়াদ শেষ হলে **401**
3. `sub` দিয়ে ডেটাবেস থেকে user আনে (token-এর role বিশ্বাস করে না, DB-র role নেয়)
4. user `is_banned` হলে **403**

**Login:** `auth/service.py` → `login()`
- আগে লক দেখে (429), তারপর Argon2 দিয়ে পাসওয়ার্ড মেলায়
- ভুল হলে `failed_login_count` বাড়ে, ৫ হলে ১৫ মিনিট লক
- ঠিক হলে `auth_session` সারি বানায়, refresh token দেয় (cookie), access token দেয় (body)

**Refresh:** `auth/service.py` → `refresh_session()`
- Cookie-র token-এর SHA-256 hash দিয়ে `auth_session` খোঁজে
- ঠিক হলে **rotation**: পুরনো hash `prev_token_hash`-এ যায়, নতুন token ও hash বসে
- পুরনো (ইতিমধ্যে ঘোরানো) token আবার এলে → চুরি ধরে নিয়ে session বাতিল (`token_reuse` log)
- ১০ সেকেন্ডের grace: দুই ট্যাবে একসাথে refresh হলে ভুল করে বাতিল না হয়

**Logout:** session-এর `revoked_at` বসে। তাই cookie থাকলেও refresh আর চলে না।

**Token expire হলে কী হয়?** `frontend/src/services/http.ts` → `request()`
- ৪০১ পেলে একবার `/auth/refresh` ডাকে (একসাথে অনেক request এলেও refresh একটাই হয়: `refreshing` promise)
- সফল হলে একই request আবার পাঠায়; ব্যর্থ হলে `onLost()` → লগআউট

**Token ব্রাউজারে কোথায় থাকে?**
- Access token: শুধু JavaScript memory (`http.ts`-এর `accessToken` ভ্যারিয়েবল), localStorage-এ না → XSS-এ চুরি কঠিন
- Refresh token: `httpOnly` cookie, `SameSite=Strict`, `Path=/api/v1/auth`, Vercel-এ `Secure`

**প্রশ্ন: Refresh token ডেটাবেসে hash করে কেন রাখা?** ডেটাবেস চুরি হলেও আসল token পাওয়া যাবে না।
**প্রশ্ন: Access token ১৫ মিনিট কেন?** চুরি গেলেও অল্প সময়ই কাজে লাগে। বেশি ছোট হলে বারবার refresh করতে হয়।
**প্রশ্ন: Pepper কী?** পাসওয়ার্ডের সাথে মেশানো সার্ভারের গোপন লেখা (`PEPPER` env)। শুধু DB চুরি হলে পাসওয়ার্ড ভাঙা কঠিন। `security.py` → `_peppered()` (HMAC-SHA256)।
**প্রশ্ন: Login-এ ইমেইল নেই আর পাসওয়ার্ড ভুল, দুটোর বার্তা এক কেন?** ইমেইল আছে কিনা বাইরের কেউ যেন বুঝতে না পারে। আর `DUMMY_HASH` দিয়ে সময়ও সমান রাখা হয়।

## ২. RBAC মডিউল

**ফাইল:** `app/rbac_constants.py` (অনুমতির নাম ও কোন role-এ কী), `app/rbac.py` (`require()`)

```python
def require(permission):
    def checker(user = Depends(get_current_user)):
        if permission not in ROLE_PERMISSIONS.get(user.role, set()):
            raise HTTPException(403, "Not enough permissions")
        return user
    return Depends(checker)
```
- Endpoint-এ ব্যবহার: `user: Annotated[User, require(P.ADMIN_USERS_BAN)]`
- Token না থাকলে `get_current_user` আগেই ৪০১ দেয়; token ঠিক কিন্তু অনুমতি নেই হলে ৪০৩ দেয়
- নতুন অনুমতি যোগ: `P`-তে নাম, `ROLE_PERMISSIONS`-এ বসানো, endpoint-এ `require(P.NEW)`

**Ownership কোথায়?** `catalog/service.py` → `can_update()`, `can_delete()`
- নিজের পণ্য (`owner_id == user.id`) → অনুমতি
- না হলে পণ্যের `group_id` দেখে `group_permissions()` ডাকে
  - `update` থাকলে সব বদল করা যায়
  - শুধু `stock` থাকলে কেবল `stock` ও `is_active` বদলানো যায় (`STOCK_FIELDS`)
- মোছা: পণ্যের মালিক অথবা গ্রুপের owner
- মালিকহীন (seed) পণ্য কোনো সাধারণ ব্যবহারকারী বদলাতে পারে না

**গ্রুপ:** `groups/service.py`
- `_member_for()`: সদস্য না হলে ৪০৪ (গ্রুপ আছে কিনাও জানতে দেয় না)
- `_owner_only()`: নাম বদলানো, গ্রুপ মোছা, সদস্য যোগ/বদল/সরানো শুধু owner → নইলে ৪০৩

**অ্যাডমিনের সুরক্ষা:** `admin/service.py`
- `change_role()`: `target.id == admin.id` হলে ৪০৩
- `ban_user()`: `target.role == "admin"` হলে ৪০৩ (নিজেকেও)
- bulk ban admin বাদ দিয়ে `skipped`-এ জানায়

**Ban হলে পরের request-ই আটকায় কেন?** `get_current_user` প্রতিবার DB থেকে user আনে ও `is_banned` দেখে। Token-এর মেয়াদের জন্য অপেক্ষা নেই। Ban-এর সময় সব session-ও বাতিল হয় (`revoke_all`)।

## ৩. "এই লাইন সরালে কী হবে?" (সম্ভাব্য প্রশ্ন)

| সরালে/বদলালে | ফল |
|---|---|
| `algorithms=["HS256"]` সরানো | token নিজের algorithm বেছে নিতে পারে (`alg=none` আক্রমণের ঝুঁকি) |
| `get_current_user`-এ `is_banned` চেক সরানো | ban করা user ১৫ মিনিট পর্যন্ত ঢুকতে পারবে |
| ownership চেক `can_update` সরানো | যে কেউ যে কারো পণ্য বদলাতে পারবে |
| `httponly=True` সরানো | JavaScript (XSS) দিয়ে refresh token চুরি সম্ভব |
| `samesite="strict"` সরানো | অন্য সাইট থেকে refresh cookie পাঠানো সম্ভব (CSRF-এর ঝুঁকি) |
| `prev_token_hash` রাখা বন্ধ করা | চোরাই পুরনো token ধরা যাবে না |
| `DUMMY_HASH` সরানো | ইমেইল আছে কিনা সময় মেপে বোঝা যাবে |
| CORS-এ `allow_origins=["*"]` দেওয়া | যেকোনো সাইট API ডাকতে পারবে (credentials সহ হলে বিপজ্জনক) |
| `ProductUpdate`-এ `owner_id` যোগ করা | কেউ নিজের পণ্য অন্যের নামে করতে পারবে (over-posting) |
| Admin CSV-তে `_safe()` সরানো | `=cmd...` লেখা সূত্র হিসেবে Excel-এ চলবে |

## ৪. ভিডিও ডেমোর ক্রম (৫–৮ মিনিট, Vercel URL-এ)

1. সাধারণ user (যেমন salma) দিয়ে লগইন, নিজের পণ্য দেখানো
2. **RBAC denial:** salma-র গ্রুপ-পণ্য খুলে দাম বদলানোর চেষ্টা (UI-তে শুধু স্টকের বক্স), তারপর `/api/docs` বা Network ট্যাবে PATCH `price` পাঠিয়ে ৪০৩ দেখানো
3. **গ্রুপ:** rahim (owner) দিয়ে সদস্য ও অনুমতি দেখানো, অনুমতি বদলানো
4. **DevTools → Network:** `Authorization` header, token মেয়াদ শেষে ৪০১ ও `/auth/refresh` (দেমোর জন্য Vercel-এ `ACCESS_TOKEN_MINUTES=1` দিতে পারেন, পরে ১৫ করে ফেলুন), Application ট্যাবে httpOnly cookie
5. admin1 দিয়ে লগইন: ড্যাশবোর্ড, ব্যবহারকারী তালিকা (search/filter), user detail
6. কারণ লিখে একজনকে **ban**, আলাদা ব্রাউজারে ওই user-এর পরের request-এ ৪০৩ দেখানো, তারপর unban
7. অ্যাক্টিভিটি লগ (login_failed, ban ইত্যাদি), নিরাপত্তা ট্যাব, CSV ডাউনলোড
8. শেষে একবার বলুন কোথায় কী কোড (`security.py`, `rbac.py`, `catalog/service.py`)

## ৫. আপনার নিজের কাজ (আমি করতে পারি না)

- [ ] রিপোর্টে নাম, ID, section, তারিখ, issue/PR লিংক বসানো
- [ ] E5-তে AI ব্যবহার সত্যি করে লেখা (কোন অংশে, আর আপনি কী যাচাই/বদলেছেন)
- [ ] S1–S21 স্ক্রিনশট নেওয়া (Vercel URL-এ) ও PDF বানানো, Appendix-এ ৫টা টেস্ট অ্যাকাউন্টের ID ও পাসওয়ার্ড
- [ ] ভিডিও রেকর্ড (নিজের কণ্ঠে) ও শেয়ার লিংক
- [ ] সব commit নিজের GitHub অ্যাকাউন্ট থেকে (`git config user.name`/`user.email` ঠিক আছে কিনা দেখুন)
- [ ] Submission form ২৮ নভেম্বরের মধ্যে (গতবার দেরি হয়েছিল!)
