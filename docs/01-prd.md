# Product Requirements Document (PRD) — Supply Mart

| Field | Value |
|---|---|
| Product | Supply Mart |
| Version | MVP + Beta |
| Releases | MVP — Mid-term, Beta — Final |
| Status | Draft |
| Related docs | Software Requirements Specification (SRS), Technical Design Document (TDD) |

This document covers both releases. Every goal, feature and story has a **Release** column, so it is clear what is built for the mid-term and what is added for the final.

**Documents in this set**

| Short form | Full form | Purpose | File |
|---|---|---|---|
| PRD | Product Requirements Document | What we build and why (this document) | `01-prd.md` |
| SRS | Software Requirements Specification | Exact requirements, permissions and acceptance criteria | `02-srs.md` |
| TDD | Technical Design Document | How we build it: architecture, data model, API | `03-tdd.md` |

## 0. Release plan

| Release | When | Focus |
|---|---|---|
| MVP | Mid-term | Core marketplace: product and order REST API, database, React pages, runs locally |
| Beta | Final | Users and permissions (auth, RBAC, security scopes), shops, dashboards, deployment on Vercel |

## 1. Purpose

Supply Mart is a small online grocery marketplace for Bangladesh. Shopkeepers list everyday items (rice, lentils, oil, vegetables, fish, meat, eggs, spices), customers add them to a cart and order with Cash on Delivery, and an admin approves shops and watches the system.

Two clear steps:

- **MVP (mid-term):** a working REST API and React pages for browsing products, managing products and placing orders.
- **Beta (final):** turn the MVP into a multi-user product with accounts, three roles (RBAC), security scopes on every protected endpoint, shops with admin approval, stock tracking, role dashboards and deployment.

## 2. Problem statement

Small shopkeepers have no simple way to put their stock online, and customers cannot compare items from several nearby shops in one place. A shared platform also needs control: only trusted shops should be visible, customers must not see each other's orders, and every user should be able to do only what their role allows.

## 3. Goals

| ID | Goal | Release |
|---|---|---|
| G-1 | Provide a REST API for products and orders that follows standard REST conventions. | MVP |
| G-2 | Store data in a database so it survives restarts. | MVP |
| G-3 | Document the API automatically (OpenAPI at `/api/docs`). | MVP |
| G-4 | Provide a React + TypeScript frontend that uses the API (browse, cart, checkout). | MVP |
| G-5 | Let users sign up and log in; protected data is available only after login. | Beta |
| G-6 | Control access with three roles: customer, shopkeeper, admin (RBAC). | Beta |
| G-7 | Enforce fine-grained permissions with security scopes on every protected endpoint. | Beta |
| G-8 | Let shopkeepers sell their own products, with admin approval and stock tracking. | Beta |
| G-9 | Give every role a dashboard and a profile page. | Beta |
| G-10 | Protect accounts and data (hashed passwords, token security, login limit). | Beta |
| G-11 | Deploy automatically to Vercel on every push to `main`. | Beta |

## 4. Target users

| User | Need | Release |
|---|---|---|
| Visitor (not logged in) | Browse and search products, fill a cart. | MVP |
| Shopkeeper (MVP demo) | Add, edit and delete products; change order status. | MVP |
| Frontend developer | A clear, documented API to build the UI on. | MVP |
| Instructor / reviewer | An easy way to try the API (`/api/docs`) and check the code. | MVP |
| Customer | Sign up, order, see own orders, edit profile. | Beta |
| Shopkeeper | Register a shop, manage own products and stock, handle orders for own items. | Beta |
| Admin | Approve shops, see users and all orders, view platform statistics. | Beta |

In the MVP there are no accounts: product and order endpoints are open so the core API can be demonstrated. In the Beta they are protected by roles and scopes.

## 5. Scope

### In scope — MVP (mid-term)

- Categories (seeded) and products: list (filter, search, sort, pagination), view, create, update, delete
- Place an order from a cart; list orders; view one order; change an order item's status
- Input validation and clear error responses
- Health check endpoint and interactive API docs at `/api/docs`
- React + TypeScript pages: product list, product details, cart, checkout, orders

### In scope — Beta (final)

- Auth: sign up (customer and shopkeeper), log in, log out, refresh session (JWT access token + refresh token)
- Profile: view my profile, change my name and phone, change my password
- RBAC: customer, shopkeeper, admin; security scopes on every protected endpoint
- Shops: shopkeeper registers a shop, admin approves or rejects it; only approved shops' products are public
- Shopkeeper: manage own products and stock, see and update orders that contain own items
- Customer: place orders only when logged in, see own orders
- Admin: list users, list shops, view all orders, update any order item
- Dashboard: role-specific statistics
- Security: hashed passwords, secure cookies, login attempt limit, security headers, secrets only in environment variables
- Deployment on Vercel with a hosted database

### Out of scope for this semester

- Online payment (bKash, cards) and real delivery tracking
- Machine Learning, AI or recommendations
- Reviews, coupons, wishlists, returns, notifications
- Email verification, password reset, social login
- Image upload (products use an emoji icon)
- Automated CI/CD pipeline (a basic test suite for 401/403 is planned in the Beta)

## 6. Features and priority (MoSCoW)

Priorities are per release: a Beta "Must" is required for the final, not for the mid-term.

| ID | Feature | Release | Priority |
|---|---|---|---|
| F-1 | List categories | MVP | Must |
| F-2 | List products (filter by category, search, sort by price, pagination) | MVP | Must |
| F-3 | Get product by ID | MVP | Must |
| F-4 | Create product | MVP | Must |
| F-5 | Update product | MVP | Must |
| F-6 | Delete product | MVP | Must |
| F-7 | Place order from a cart (Cash on Delivery) | MVP | Must |
| F-8 | List orders and get order by ID | MVP | Must |
| F-9 | Update order item status | MVP | Should |
| F-10 | Validation and error responses | MVP | Must |
| F-11 | Health check and API docs | MVP | Must |
| F-12 | React pages that use the API (browse, cart, checkout, orders) | MVP | Should |
| F-13 | Sign up, log in, log out, refresh session | Beta | Must |
| F-14 | Roles customer / shopkeeper / admin (RBAC) | Beta | Must |
| F-15 | Security scopes on every protected endpoint | Beta | Must |
| F-16 | Shop registration and admin approval | Beta | Must |
| F-17 | Shopkeeper: manage own products | Beta | Must |
| F-18 | Orders per role (customer own, shopkeeper own items, admin all) | Beta | Must |
| F-19 | Stock tracking on order | Beta | Should |
| F-20 | Profile (view, change name/phone, change password) | Beta | Should |
| F-21 | Role-specific dashboard | Beta | Should |
| F-22 | Security hardening (hashing, cookies, login limit, headers) | Beta | Must |
| F-23 | React pages for login, shop panel, admin panel, dashboard | Beta | Should |
| F-24 | Deployment on Vercel | Beta | Must |

## 7. User stories

### MVP

| ID | Story | Feature |
|---|---|---|
| US-01 | As a visitor, I want to browse products by category, so I can see what is for sale. | F-1, F-2 |
| US-02 | As a visitor, I want to search and sort products by price, so I find items quickly. | F-2 |
| US-03 | As a visitor, I want to open one product, so I can see its details. | F-3 |
| US-04 | As a shopkeeper, I want to add a product, so customers can buy it. | F-4 |
| US-05 | As a shopkeeper, I want to edit a product's price and stock, so my catalogue stays correct. | F-5 |
| US-06 | As a shopkeeper, I want to delete a product, so removed items disappear. | F-6 |
| US-07 | As a customer, I want to put products in a cart and place an order with my name, phone and address, so I can buy with Cash on Delivery. | F-7, F-12 |
| US-08 | As a shopkeeper or admin, I want to see orders and change an order item's status, so customers know the progress. | F-8, F-9 |
| US-09 | As a client developer, I want clear error messages, so I know what went wrong. | F-10 |
| US-10 | As a maintainer, I want a health endpoint and API docs, so I can check the deploy and try the API. | F-11 |

### Beta

| ID | Story | Feature |
|---|---|---|
| US-11 | As a visitor, I want to sign up as a customer, so I can place orders. | F-13 |
| US-12 | As a visitor, I want to sign up as a shopkeeper with my shop details, so I can sell products. | F-13, F-16 |
| US-13 | As a user, I want to log in and log out, so only I can use my account. | F-13 |
| US-14 | As a customer, I want to see only my own orders, so my purchases stay private. | F-18 |
| US-15 | As a shopkeeper, I want to manage only my own products, so other shops' data is safe. | F-17 |
| US-16 | As a shopkeeper, I want to see only the orders that contain my items and update their status. | F-18 |
| US-17 | As an admin, I want to approve or reject shops, so only trusted shops are visible. | F-16 |
| US-18 | As an admin, I want to list users and view all orders, so I can monitor the platform. | F-14, F-18 |
| US-19 | As the system owner, I want every protected endpoint to need the right scope, so users cannot do more than their role allows. | F-14, F-15 |
| US-20 | As a shopkeeper, I want stock to decrease when an order is placed, so customers cannot buy unavailable items. | F-19 |
| US-21 | As a user, I want a profile page where I can change my name, phone and password. | F-20 |
| US-22 | As a user, I want a dashboard with numbers about my role (my orders, my products, platform totals). | F-21 |
| US-23 | As a user, I want my password stored safely and repeated wrong logins blocked, so my account is hard to break into. | F-22 |

## 8. Success metrics

### MVP

- All core endpoints (categories, products, orders, order-item status) work locally and are listed at `/api/docs`.
- A visitor can complete browse → cart → checkout in the React app.
- Data is still there after restarting the server.

### Beta

- A customer can never read another customer's order; a shopkeeper can never change another shop's product or order item.
- Every protected endpoint rejects a missing token with `401` and a missing scope with `403` (checked by automated tests).
- Only approved shops' products are visible to the public.
- Passwords are never stored or returned in plain text.
- The public Vercel URL works for all three roles.

## 9. Assumptions and constraints

- The frontend is Vite + React + TypeScript; the backend is Python 3.10+ with FastAPI (from the course template).
- Hosted on Vercel (frontend and backend in one project, see `vercel.json`).
- Vercel functions are serverless, so production data must live in an external database (Supabase PostgreSQL), not a local file. Locally, SQLite is used.
- Payment is Cash on Delivery only; delivery is not tracked.
- Categories are fixed and seeded.
- The first admin is created by a seed script, never through public sign-up.
- MVP demo data does not need to be kept when the Beta adds user ownership.

## 10. Milestones

### MVP — Mid-term

| Milestone | Deliverable |
|---|---|
| M1 — Docs | PRD, SRS and TDD (covering MVP and Beta) |
| M2 — Data layer | Models for category, product, order, order item; seed data; database connection |
| M3 — API | Products, categories and orders endpoints with validation |
| M4 — Mid demo | React pages (browse, cart, checkout, orders) working with the API locally, tagged `v0.1.0` (MVP) |

### Beta — Final

| Milestone | Deliverable |
|---|---|
| B1 — Auth | Migrations in place; sign up, log in, log out, refresh, profile; orders owned by users |
| B2 — RBAC + scopes | Roles, scopes, permission checks on every endpoint, admin seed script |
| B3 — Shops | Shop registration, admin approval, shopkeeper product and order panel, stock tracking |
| B4 — Security + dashboard | Password hashing, secure cookies, login limit, security headers, dashboards, 401/403 tests |
| B5 — Final demo | Beta live on Vercel, tagged `v0.2.0` (Beta) |

## 11. Release dependencies

- The Beta is built on top of the MVP: the same `/api/v1/products` and `/api/v1/orders` resources stay. In the Beta the write endpoints require login and the right scope, and orders belong to a user.
- Database migrations (Alembic) start at the beginning of the Beta, so the schema can grow from four tables to seven without manual SQL.
- <!-- PRD documentation update -->
