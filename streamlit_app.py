"""
BasketPilot — Streamlit deployment (Streamlit Community Cloud compatible).

Calls the recommendation engine in-process via TestClient — no browser → localhost
connection (which fails on Streamlit Cloud).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "src" / "phase2" / "frontend"
sys.path.insert(0, str(ROOT))

DEMO_USER = "user_001"

USUAL_PICKS = [
    {"id": "milk-amul-1l", "name": "Amul Taaza 1L", "price": 56, "emoji": "🥛", "category": "Milk"},
    {"id": "bread-brown", "name": "Brown Bread", "price": 45, "emoji": "🍞", "category": "Bread"},
    {"id": "fruit-banana", "name": "Banana 6 pcs", "price": 40, "emoji": "🍌", "category": "Fruits"},
    {"id": "milk-mother-500", "name": "Mother Dairy 500ml", "price": 28, "emoji": "🥛", "category": "Milk"},
    {"id": "bread-pav", "name": "Pav (6 pcs)", "price": 30, "emoji": "🍞", "category": "Bread"},
    {"id": "fruit-apple", "name": "Apple 1kg", "price": 180, "emoji": "🍎", "category": "Fruits"},
]

AI_CART_ID = "ai-discovery-pick"


def _load_secrets_into_env() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in ("GROK_API_KEY", "GROQ_API_KEY", "GROK_MODEL", "USE_LLM", "SURVEY_PDF_PATH", "APP_ENV"):
        if key in secrets:
            os.environ[key] = str(secrets[key])


@st.cache_resource(show_spinner="Starting BasketPilot…")
def get_api_client():
    _load_secrets_into_env()
    from starlette.testclient import TestClient
    from src.app.main import app

    return TestClient(app)


def api_post(path: str, payload: dict) -> dict:
    client = get_api_client()
    r = client.post(path, json=payload)
    r.raise_for_status()
    return r.json()


def _init_state():
    defaults = {
        "page": "home",
        "cart": [],
        "recommendation": None,
        "insights": {"categories": 0, "savings": 0, "coins": 0, "orders": 12},
        "ai_added_once": False,
        "show_rating": False,
        "show_success": False,
        "show_ai_remind": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _cart_count() -> int:
    return sum(i["quantity"] for i in st.session_state.cart)


def _cart_subtotal() -> int:
    return sum(i["price"] * i["quantity"] for i in st.session_state.cart)


def _ai_in_cart() -> bool:
    return any(i.get("is_new") for i in st.session_state.cart)


def _add_item(product: dict, is_new: bool = False, qty: int = 1):
    for item in st.session_state.cart:
        if item["id"] == product["id"]:
            item["quantity"] += qty
            return
    st.session_state.cart.append(
        {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "category": product["category"],
            "emoji": product.get("emoji", "🛒"),
            "quantity": qty,
            "is_new": is_new,
        }
    )


def _load_recommendation():
    if st.session_state.recommendation:
        return
    try:
        data = api_post("/api/v1/phase2/cards", {"user_id": DEMO_USER})
        st.session_state.recommendation = data.get("recommendation")
    except Exception as exc:
        st.session_state.rec_error = str(exc)


def _inject_css():
    css = FRONTEND / "styles.css"
    if css.exists():
        st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def _header():
    count = _cart_count()
    st.markdown(
        f"""
        <div class="web-header" style="border-radius:0;margin:-1rem -1rem 0 -1rem;">
          <div class="web-header-top">
            <div class="brand">
              <span class="pilot-badge">PILOT</span>
              <span class="brand-name">BasketPilot</span>
              <span class="brand-tagline">Smart Discovery</span>
            </div>
            <span style="color:#64748b;font-size:0.8rem;">⚡ 8 min · Cart: {count} · ₹{_cart_subtotal()}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _bottom_nav():
    pages = [
        ("home", "🏠", "Home"),
        ("discover", "✨", "Discover"),
        ("cart", "🛒", "Checkout"),
        ("insights", "📊", "Insights"),
    ]
    cols = st.columns(4)
    for col, (pid, icon, label) in zip(cols, pages):
        with col:
            active = st.session_state.page == pid
            if st.button(
                f"{icon} {label}",
                key=f"nav_{pid}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.page = pid
                st.rerun()


def _page_home():
    _load_recommendation()
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    st.markdown(f"### {greeting}, Priya 👋")
    st.caption("Add usual picks + your AI discovery pick in one checkout")

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("#### 🛒 Your usual picks")
        st.markdown(
            """
            <div style="border:2px solid #ddd6fe;border-radius:12px;background:linear-gradient(180deg,#faf5ff,#fff);
            padding:8px;max-height:220px;overflow-y:auto;">
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, p in enumerate(USUAL_PICKS):
            with cols[i % 2]:
                if st.button(f"{p['emoji']} {p['name']} · ₹{p['price']}", key=f"pick_{p['id']}", use_container_width=True):
                    _add_item(p)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("#### ✨ Your Discovery Pick (MVP core)")
        rec = st.session_state.recommendation
        if rec:
            st.markdown(f"**{rec.get('category', '')}**")
            st.markdown(rec.get("headline", ""))
            st.info(rec.get("reason", ""))
            products = rec.get("products") or []
            if products:
                p0 = products[0]
                st.markdown(f"✨ **{p0.get('name')}** · ₹{p0.get('price_inr')}")
            if st.button("+ Add AI pick to cart", type="primary", key="add_ai_home"):
                p0 = (rec.get("products") or [{}])[0]
                _add_item(
                    {
                        "id": AI_CART_ID,
                        "name": p0.get("name", "AI pick"),
                        "price": p0.get("price_inr", 0),
                        "category": rec.get("category", "AI"),
                        "emoji": "✨",
                    },
                    is_new=True,
                )
                if not st.session_state.ai_added_once:
                    st.session_state.insights["categories"] += 1
                    st.session_state.insights["coins"] += 50
                    st.session_state.ai_added_once = True
                st.rerun()
        else:
            st.warning("Loading recommendation… refresh if this persists.")

    if _cart_count() > 0:
        if st.button(f"Proceed to Checkout → ({_cart_count()} items · ₹{_cart_subtotal()})", type="primary"):
            st.session_state.page = "cart"
            st.rerun()


def _page_discover():
    _load_recommendation()
    rec = st.session_state.recommendation
    if not rec:
        st.warning("No recommendation available.")
        return
    st.markdown(f"### {rec.get('category')}")
    st.markdown(rec.get("headline"))
    st.info(rec.get("reason"))
    st.caption(rec.get("trust_signal", ""))
    for p in rec.get("products") or []:
        st.markdown(f"- **{p.get('name')}** · ₹{p.get('price_inr')} · ★ {p.get('rating')}")
    if rec.get("price_comparison_note"):
        st.success(rec["price_comparison_note"])
    if st.button("One-click Add to Cart", type="primary"):
        p0 = (rec.get("products") or [{}])[0]
        _add_item(
            {
                "id": AI_CART_ID,
                "name": p0.get("name", "AI pick"),
                "price": p0.get("price_inr", 0),
                "category": rec.get("category", "AI"),
                "emoji": "✨",
            },
            is_new=True,
        )
        st.rerun()


def _page_cart():
    st.markdown("### 🛍️ Checkout")
    if not st.session_state.cart:
        st.info("Cart is empty — add items from Home.")
        if st.button("Back to Home"):
            st.session_state.page = "home"
            st.rerun()
        return

    for item in st.session_state.cart:
        c1, c2, c3 = st.columns([4, 1, 1])
        tag = "✨ AI" if item.get("is_new") else "Habit"
        with c1:
            st.markdown(f"{item['emoji']} **{item['name']}** ({tag}) · ₹{item['price']} each")
        with c2:
            st.markdown(f"× **{item['quantity']}**")
        with c3:
            st.markdown(f"**₹{item['price'] * item['quantity']}**")

    if not _ai_in_cart() and st.session_state.recommendation:
        st.warning("Try your AI discovery pick before checkout!")
        if st.button("+ Add AI pick"):
            rec = st.session_state.recommendation
            p0 = (rec.get("products") or [{}])[0]
            _add_item(
                {
                    "id": AI_CART_ID,
                    "name": p0.get("name", "AI pick"),
                    "price": p0.get("price_inr", 0),
                    "category": rec.get("category", "AI"),
                    "emoji": "✨",
                },
                is_new=True,
            )
            st.rerun()

    bonus = 25 if _ai_in_cart() else 0
    total = max(_cart_subtotal() - bonus, 0)
    st.markdown(f"**Subtotal:** ₹{_cart_subtotal()}")
    if bonus:
        st.markdown(f"**New category bonus:** -₹{bonus}")
    st.markdown(f"### Total: ₹{total}")

    if st.button("Place Order →", type="primary"):
        if not _ai_in_cart() and st.session_state.recommendation:
            st.session_state.show_ai_remind = True
        else:
            _finish_order()


def _finish_order():
    total = max(_cart_subtotal() - (25 if _ai_in_cart() else 0), 0)
    st.session_state.insights["orders"] += 1
    st.session_state.insights["coins"] += 25
    if _ai_in_cart():
        st.session_state.insights["categories"] += 1
        try:
            api_post(
                "/api/v1/phase3/feedback",
                {
                    "user_id": DEMO_USER,
                    "recommendation_id": (st.session_state.recommendation or {}).get("recommendation_id"),
                    "rating": 5,
                    "added_to_cart": True,
                    "purchased": True,
                    "variant": "treatment",
                },
            )
        except Exception:
            pass
        st.session_state.show_rating = True
    st.session_state.order_message = f"{_cart_count()} items purchased · ₹{total} paid"
    st.session_state.cart = []
    st.session_state.ai_added_once = False
    st.session_state.show_success = True


def _page_insights():
    ins = st.session_state.insights
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("New categories", ins["categories"])
    c2.metric("Time saved", "~12 min")
    c3.metric("Saved vs competitors", f"₹{ins['savings']}")
    c4.metric("Pilot Coins", ins["coins"])


def main():
    st.set_page_config(page_title="BasketPilot", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")
    _init_state()
    _inject_css()

    st.markdown(
        """
        <style>
          header[data-testid="stHeader"] { display: none; }
          #MainMenu { visibility: hidden; }
          footer { visibility: hidden; }
          .stApp { background: #f8fafc; }
          .block-container { padding-top: 1rem; max-width: 1200px; padding-bottom: 1.5rem; }
          div[data-testid="stHorizontalBlock"]:has(button[kind="primary"]) button,
          div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button {
            font-size: 0.78rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        client = get_api_client()
        health = client.get("/health")
        if health.status_code != 200:
            st.error("Backend failed to start.")
            st.stop()
    except Exception as exc:
        st.error(f"Connection failure: {exc}")
        st.info("Ensure requirements are installed and survey PDF exists at data/survey/responses.pdf")
        st.stop()

    _header()

    if st.session_state.show_success:
        st.success(f"🎉 Order placed! {st.session_state.get('order_message', '')}")
        if st.button("Continue"):
            st.session_state.show_success = False
            st.session_state.page = "home"
            st.rerun()

    if st.session_state.show_ai_remind:
        st.warning("Try your AI Discovery Pick? This MVP is built around one smart recommendation.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Proceed without AI pick"):
                st.session_state.show_ai_remind = False
                _finish_order()
                st.rerun()
        with c2:
            if st.button("Go back"):
                st.session_state.show_ai_remind = False
                st.rerun()

    if st.session_state.show_rating:
        st.markdown("### How was your Discovery Pilot? 🌟")
        rating = st.slider("Rating", 1, 5, 5)
        if st.button("Submit feedback"):
            st.session_state.show_rating = False
            st.session_state.page = "insights"
            st.rerun()

    page = st.session_state.page
    if page == "home":
        _page_home()
    elif page == "discover":
        _page_discover()
    elif page == "cart":
        _page_cart()
    elif page == "insights":
        _page_insights()

    st.markdown("---")
    _bottom_nav()


main()
