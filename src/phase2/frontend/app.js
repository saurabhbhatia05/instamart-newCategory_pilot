/**
 * BasketPilot — Discovery Pilot Demo
 * Home = AI hero + compact usual picks (combined cart)
 */

const DEMO_USER = "user_001";

const USUAL_PICKS = {
  milk: [
    { id: "milk-amul-1l", name: "Amul Taaza 1L", price: 56, emoji: "🥛", category: "Milk" },
    { id: "milk-mother-500", name: "Mother Dairy 500ml", price: 28, emoji: "🥛", category: "Milk" },
  ],
  bread: [
    { id: "bread-brown", name: "Brown Bread", price: 45, emoji: "🍞", category: "Bread" },
    { id: "bread-pav", name: "Pav (6 pcs)", price: 30, emoji: "🍞", category: "Bread" },
  ],
  fruit: [
    { id: "fruit-banana", name: "Banana 6 pcs", price: 40, emoji: "🍌", category: "Fruits" },
    { id: "fruit-apple", name: "Apple 1kg", price: 180, emoji: "🍎", category: "Fruits" },
  ],
};

const ALL_PRODUCTS = Object.values(USUAL_PICKS).flat();

const REORDER_DEFAULTS = [
  USUAL_PICKS.milk[0],
  USUAL_PICKS.bread[0],
  USUAL_PICKS.fruit[0],
];

const AI_CART_ID = "ai-discovery-pick";

let recommendation = null;
let cartItems = [];
let insights = { categories: 0, savings: 0, coins: 0, orders: 12 };
let activePickFilter = "all";
let searchQuery = "";
let aiAddedOnce = false;
let pendingPostPurchaseRating = false;
let lastCheckoutHadAi = false;

const $ = (id) => document.getElementById(id);

function showToast(msg, type = "") {
  const t = $("toast");
  t.textContent = msg;
  t.className = `toast ${type}`.trim();
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 2800);
}

function getCartItemCount() {
  return cartItems.reduce((sum, item) => sum + item.quantity, 0);
}

function getCartSubtotal() {
  return cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

function getNewCategoryBonus() {
  return cartItems.some((item) => item.isNew) ? 25 : 0;
}

function getAiCartItem() {
  return cartItems.find((item) => item.isNew);
}

function getHabitCount() {
  return cartItems.filter((item) => !item.isNew).reduce((s, i) => s + i.quantity, 0);
}

function findCartItem(id) {
  return cartItems.find((item) => item.id === id);
}

function addCartItem(product, { isNew = false, quantity = 1 } = {}) {
  const existing = findCartItem(product.id);
  if (existing) {
    existing.quantity += quantity;
  } else {
    cartItems.push({
      id: product.id,
      name: product.name,
      price: product.price,
      category: product.category,
      emoji: product.emoji || "🛒",
      quantity,
      isNew,
    });
  }
  updateCartBadge();
  renderHome();
  renderCart();
}

function updateCheckoutBar() {
  const total = getCartItemCount();
  const bar = $("home-checkout-bar");
  if (!bar) return;

  if (total > 0) {
    bar.classList.remove("hidden");
    $("checkout-bar-count").textContent = `${total} item${total > 1 ? "s" : ""}`;
    $("checkout-bar-total").textContent = `₹${Math.max(getCartSubtotal() - getNewCategoryBonus(), 0)}`;
  } else {
    bar.classList.add("hidden");
  }
}

function changeQuantity(id, delta) {
  const item = findCartItem(id);
  if (!item) return;

  item.quantity += delta;
  if (item.quantity <= 0) {
    cartItems = cartItems.filter((i) => i.id !== id);
  }

  updateCartBadge();
  renderCart();
  renderHome();
}

function clearCart() {
  cartItems = [];
  aiAddedOnce = false;
  updateCartBadge();
  renderCart();
  renderHome();
  updateAiButtons(false);
}

function updateCartBadge() {
  const count = getCartItemCount();
  $("cart-count").textContent = count;
  $("cart-count").classList.toggle("hidden", count === 0);
}

function updateAiButtons(inCart) {
  const aiQty = getAiCartItem()?.quantity || 0;
  ["btn-add-cart", "btn-add-ai-home"].forEach((id) => {
    const btn = $(id);
    if (!btn) return;
    if (inCart || aiQty > 0) {
      btn.textContent = aiQty > 1 ? `✓ AI pick in cart (${aiQty})` : "✓ AI pick in cart";
      btn.classList.add("added");
    } else {
      btn.textContent = id === "btn-add-ai-home" ? "+ Add AI pick to cart" : "One-click Add to Cart";
      btn.classList.remove("added");
    }
  });
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning, Priya ☀️";
  if (hour < 17) return "Good afternoon, Priya 🌤️";
  return "Good evening, Priya 🌙";
}

function renderHome() {
  $("greeting-time").textContent = getGreeting();

  const habitN = getHabitCount();
  const aiN = getAiCartItem()?.quantity || 0;
  const total = getCartItemCount();
  const subtotal = getCartSubtotal();

  if (total > 0) {
    const parts = [];
    if (habitN) parts.push(`${habitN} usual`);
    if (aiN) parts.push(`${aiN} AI`);
    $("greeting-sub").textContent = `${parts.join(" + ")} in cart · ₹${subtotal} — checkout together`;
  } else {
    $("greeting-sub").textContent = "Add usual picks above, then your AI pick — checkout together";
  }

  const chip = $("home-cart-chip");
  if (total > 0) {
    chip.classList.remove("hidden");
    $("home-cart-chip-text").textContent = `${total} · ₹${subtotal}`;
  } else {
    chip.classList.add("hidden");
  }

  renderQuickPicks();
  updateAiButtons(aiN > 0);
  updateCheckoutBar();
}

function renderQuickPicks() {
  const container = $("quick-picks");
  let products = [
    USUAL_PICKS.milk[0],
    USUAL_PICKS.bread[0],
    USUAL_PICKS.fruit[0],
    USUAL_PICKS.milk[1],
    USUAL_PICKS.bread[1],
    USUAL_PICKS.fruit[1],
  ];

  if (activePickFilter !== "all") {
    products = USUAL_PICKS[activePickFilter] || [];
  }

  container.innerHTML = products
    .map((p) => {
      const inCart = findCartItem(p.id);
      const qty = inCart?.quantity || 0;
      return `
    <button type="button" class="pick-card web-pick-card${qty ? " in-cart" : ""}" data-add-id="${p.id}">
      <span class="pick-emoji">${p.emoji}</span>
      <span class="pick-name">${p.name}</span>
      <span class="pick-price">₹${p.price}</span>
      <span class="pick-add">${qty ? "In cart · " + qty : "+ Add"}</span>
    </button>`;
    })
    .join("");
}

function searchProducts(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return ALL_PRODUCTS.filter(
    (p) =>
      p.name.toLowerCase().includes(q) ||
      p.category.toLowerCase().includes(q)
  );
}

function openSearchLayer() {
  $("search-layer")?.classList.remove("hidden");
  $("phone-frame")?.classList.add("search-active");
}

function closeSearchLayer() {
  $("search-layer")?.classList.add("hidden");
  $("phone-frame")?.classList.remove("search-active");
}

function renderSearchResults(results) {
  const panel = $("search-results");
  const clearBtn = $("search-clear");

  if (!searchQuery.trim()) {
    closeSearchLayer();
    clearBtn?.classList.add("hidden");
    if (panel) panel.innerHTML = "";
    return;
  }

  openSearchLayer();
  clearBtn?.classList.remove("hidden");

  if (results.length === 0) {
    panel.innerHTML = `<div class="search-empty">No results for "${searchQuery}"</div>`;
    return;
  }

  const hint = `<div class="search-hint">👆 Tap any item to add it directly to your cart</div>`;
  panel.innerHTML =
    hint +
    results
      .map(
        (p) => `
    <button type="button" class="search-result" data-add-id="${p.id}">
      <span>${p.emoji}</span>
      <div class="search-result-info">
        <strong>${p.name}</strong>
        <small>${p.category}</small>
      </div>
      <span class="search-result-price">₹${p.price}</span>
    </button>`
      )
      .join("");
}

function goToScreen(name) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));

  const screen = $(`screen-${name}`);
  const nav = document.querySelector(`.nav-item[data-screen="${name}"]`);
  if (screen) screen.classList.add("active");
  if (nav) nav.classList.add("active");

  $("delivery-pill").textContent =
    name === "home" ? "⚡ 8 min delivery" : `⚡ 8 min · ${name.charAt(0).toUpperCase() + name.slice(1)}`;

  closeSearch();

  if (name === "home") renderHome();
  if (name === "discover" && !recommendation) loadSmartDiscovery();
  if (name === "cart") renderCart();
  if (name === "insights") renderInsights();
}

function closeSearch() {
  $("search-input").value = "";
  searchQuery = "";
  closeSearchLayer();
  renderSearchResults([]);
}

async function loadSmartDiscovery() {
  const loaders = ["loading", "home-ai-loading"];
  loaders.forEach((id) => $(id)?.classList.remove("hidden"));
  $("discovery-card")?.classList.add("hidden");
  $("home-ai-card")?.classList.add("hidden");
  $("card-error")?.classList.add("hidden");
  $("home-ai-error")?.classList.add("hidden");

  try {
    let data = window.__INITIAL_CARDS__ || null;
    if (!data) {
      const res = await fetch("/api/v1/phase2/cards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: DEMO_USER }),
      });
      data = await res.json();
    }

    loaders.forEach((id) => $(id)?.classList.add("hidden"));

    if (!data.recommendation) {
      $("card-error")?.classList.remove("hidden");
      $("home-ai-error")?.classList.remove("hidden");
      return;
    }

    recommendation = data.recommendation;
    renderDiscoveryCard(recommendation);
    renderHomeAiCard(recommendation);
    $("demo-meta").textContent = `${data.latency_ms || 0}ms · Pilot AI`;
    $("discovery-card")?.classList.remove("hidden");
    $("home-ai-card")?.classList.remove("hidden");
    renderHome();
  } catch {
    loaders.forEach((id) => $(id)?.classList.add("hidden"));
    $("card-error")?.classList.remove("hidden");
    $("home-ai-error")?.classList.remove("hidden");
    $("demo-meta").textContent = window.__STREAMLIT_MODE__ ? "Streamlit embed" : "Backend offline";
  }
}

function renderHomeAiCard(rec) {
  const product = rec.products?.[0];
  $("home-category").textContent = rec.category;
  $("home-headline").textContent = rec.headline;
  $("home-reason").textContent = rec.reason;
  $("home-trust").textContent = rec.trust_signal || "";

  if (product) {
    $("home-product").innerHTML = `
      <span class="home-prod-emoji">✨</span>
      <div>
        <strong>${product.name}</strong>
        <span>★ ${product.rating} · ₹${product.price_inr}</span>
      </div>`;
  }

  const priceEl = $("home-price");
  if (rec.price_comparison_note) {
    priceEl.textContent = "💰 " + rec.price_comparison_note;
    priceEl.classList.remove("hidden");
  } else {
    priceEl.textContent = "";
    priceEl.classList.add("hidden");
  }
}

function renderDiscoveryCard(rec) {
  $("disc-category").textContent = rec.category;
  $("disc-headline").textContent = rec.headline;
  $("disc-reason").textContent = rec.reason;
  $("disc-context").textContent = rec.context;
  $("disc-trust").textContent = rec.trust_signal;

  $("disc-products").innerHTML = (rec.products || [])
    .map(
      (p) => `
    <div class="product-row">
      <div class="product-info">
        <div class="name">${p.name}</div>
        <div class="rating">${"★".repeat(Math.round(p.rating))} ${p.rating}</div>
      </div>
      <div class="product-price">
        <div class="price">₹${p.price_inr}</div>
        ${p.mrp_inr ? `<div class="mrp">₹${p.mrp_inr}</div>` : ""}
      </div>
    </div>`
    )
    .join("");

  const bundleEl = $("disc-bundle");
  bundleEl.innerHTML = `<span class="bundle-label">🎁 Bundle:</span>`;
  (rec.bundle_items || []).forEach((item) => {
    const tag = document.createElement("span");
    tag.className = "bundle-tag";
    tag.textContent = item;
    bundleEl.appendChild(tag);
  });

  $("disc-rewards").innerHTML = (rec.rewards || [])
    .map((r) => `<span class="reward-tag">${r.label}: ${r.value}</span>`)
    .join("");

  const priceEl = $("disc-price");
  if (rec.price_comparison_note) {
    priceEl.textContent = "💰 " + rec.price_comparison_note;
    priceEl.classList.remove("hidden");
  } else {
    priceEl.classList.add("hidden");
  }
}

function renderCart() {
  const empty = $("cart-empty");
  const list = $("cart-items");
  const summary = $("cart-summary");

  if (cartItems.length === 0) {
    empty.classList.remove("hidden");
    list.classList.add("hidden");
    summary.classList.add("hidden");
    $("cart-subtitle").textContent = "Habit items + AI discovery in one checkout";
    return;
  }

  empty.classList.add("hidden");
  list.classList.remove("hidden");
  summary.classList.remove("hidden");

  const habitN = getHabitCount();
  const aiN = getAiCartItem()?.quantity || 0;
  const parts = [];
  if (habitN) parts.push(`${habitN} usual`);
  if (aiN) parts.push(`${aiN} AI pick`);
  $("cart-subtitle").textContent = parts.join(" + ") + " — one combined order";

  list.innerHTML = cartItems
    .map(
      (item) => `
    <div class="cart-item ${item.isNew ? "cart-item-ai" : ""}">
      <div class="cart-item-left">
        <span class="cart-emoji">${item.emoji}</span>
        <div>
          ${item.isNew ? '<span class="tag">✨ AI PICK</span>' : '<span class="tag tag-habit">HABIT</span>'}
          <div class="cart-item-name">${item.name}</div>
          <small class="cart-item-cat">${item.category}</small>
          <div class="cart-line-price">₹${item.price} each</div>
        </div>
      </div>
      <div class="cart-item-right">
        <div class="qty-control">
          <button type="button" class="qty-btn" data-qty-id="${item.id}" data-delta="-1" aria-label="Decrease">−</button>
          <span class="qty-val">${item.quantity}</span>
          <button type="button" class="qty-btn" data-qty-id="${item.id}" data-delta="1" aria-label="Increase">+</button>
        </div>
        <div class="cart-line-total">₹${item.price * item.quantity}</div>
      </div>
    </div>`
    )
    .join("");

  const subtotal = getCartSubtotal();
  const bonus = getNewCategoryBonus();
  $("cart-subtotal").textContent = `₹${subtotal}`;
  $("cart-bonus").textContent = bonus ? `-₹${bonus}` : "-₹0";
  $("bonus-row").classList.toggle("hidden", bonus === 0);
  $("cart-total").textContent = `₹${Math.max(subtotal - bonus, 0)}`;

  const nudge = $("cart-ai-nudge");
  const hasAi = !!getAiCartItem();
  if (nudge) {
    nudge.classList.toggle("hidden", hasAi || !recommendation);
    if (recommendation && !hasAi) {
      $("cart-ai-nudge-text").textContent =
        `Try ${recommendation.category} — your AI discovery pick!`;
    }
  }
}

function renderInsights() {
  $("ins-categories").textContent = insights.categories;
  $("ins-savings").textContent = `₹${insights.savings}`;
  $("ins-coins").textContent = insights.coins;
  const pct = Math.min(15, insights.categories * 5 + 5);
  $("progress-fill").style.width = `${pct * 2.3}%`;
  $("progress-label").textContent = `Pilot progress: ${pct}% toward +15% target`;
}

function getProductById(id) {
  return ALL_PRODUCTS.find((p) => p.id === id);
}

function handleAddProduct(id) {
  const product = getProductById(id);
  if (!product) return;

  addCartItem(product, { isNew: false, quantity: 1 });
  showToast(`${product.emoji} ${product.name} added!`, "success");
  closeSearch();

  if (document.querySelector(".screen.active")?.id === "screen-cart") {
    renderCart();
  }
}

async function addAiToCart() {
  if (!recommendation) return;

  const product = recommendation.products?.[0];
  if (product) {
    addCartItem(
      {
        id: AI_CART_ID,
        name: product.name,
        price: product.price_inr,
        category: recommendation.category,
        emoji: "✨",
      },
      { isNew: true, quantity: 1 }
    );
  }

  aiAddedOnce = true;
  updateAiButtons(true);
  showToast("✨ AI pick added — ready for checkout!", "success");
  await submitFeedback(5, true, false);
}

async function submitFeedback(rating, addedToCart, purchased) {
  if (!recommendation) return;
  if (window.__STREAMLIT_MODE__) return;
  try {
    await fetch("/api/v1/phase3/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: DEMO_USER,
        recommendation_id: recommendation.recommendation_id,
        rating,
        added_to_cart: addedToCart,
        purchased,
        variant: "treatment",
      }),
    });
  } catch { /* demo */ }
}

function showRatingSheet() {
  document.querySelectorAll("#rating-stars button").forEach((btn) => btn.classList.remove("active"));
  $("rating-overlay").classList.remove("hidden");
}

function hideRatingSheet() {
  $("rating-overlay").classList.add("hidden");
}

function showAiRemindOverlay() {
  if (recommendation) {
    $("remind-rec-text").textContent =
      `"${recommendation.headline}" — ${recommendation.category}`;
  }
  $("ai-remind-overlay").classList.remove("hidden");
}

function hideAiRemindOverlay() {
  $("ai-remind-overlay").classList.add("hidden");
}

function goToCheckoutScreen() {
  if (getCartItemCount() === 0) {
    showToast("Cart is empty — add items first", "");
    return;
  }
  goToScreen("cart");
}

function initiateCheckout() {
  if (getCartItemCount() === 0) {
    showToast("Cart is empty — add items first", "");
    return;
  }

  if (!getAiCartItem() && recommendation) {
    showAiRemindOverlay();
    return;
  }

  finishCheckout();
}

function finishCheckout() {
  hideAiRemindOverlay();

  const itemCount = getCartItemCount();
  const total = Math.max(getCartSubtotal() - getNewCategoryBonus(), 0);
  lastCheckoutHadAi = !!getAiCartItem();

  if (lastCheckoutHadAi) {
    insights.categories += 1;
    insights.coins += 50;
    if (recommendation?.price_comparison_note) {
      const match = recommendation.price_comparison_note.match(/₹(\d+)/);
      if (match) insights.savings += parseInt(match[1], 10);
    }
  }

  insights.orders += 1;
  insights.coins += 25;

  $("success-message").textContent =
    itemCount > 0
      ? `${itemCount} item${itemCount > 1 ? "s" : ""} purchased · ₹${total} paid`
      : "Your groceries are on the way";

  pendingPostPurchaseRating = lastCheckoutHadAi;

  clearCart();
  $("success-overlay").classList.remove("hidden");
}

function onSuccessContinue() {
  $("success-overlay").classList.add("hidden");

  if (pendingPostPurchaseRating) {
    pendingPostPurchaseRating = false;
    showRatingSheet();
    return;
  }

  goToScreen("home");
}

function onRatingComplete(rating) {
  submitFeedback(rating, true, true);
  hideRatingSheet();
  showToast("Thanks for your feedback! ⭐", "success");
  setTimeout(() => goToScreen("insights"), 600);
}

function onRatingSkip() {
  if (lastCheckoutHadAi) submitFeedback(3, true, true);
  hideRatingSheet();
  goToScreen("home");
}

function reorderAll() {
  REORDER_DEFAULTS.forEach((p) => addCartItem(p, { quantity: 1 }));
  showToast("↻ Usual picks added — now add your AI pick!", "success");
}

// Nav
document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => goToScreen(btn.dataset.screen));
});

document.querySelectorAll("[data-go]").forEach((el) => {
  el.addEventListener("click", () => goToScreen(el.dataset.go));
});

$("btn-add-cart").addEventListener("click", addAiToCart);
$("btn-add-ai-home").addEventListener("click", addAiToCart);
$("btn-cart-add-ai").addEventListener("click", addAiToCart);
$("btn-checkout").addEventListener("click", initiateCheckout);
$("btn-home-checkout").addEventListener("click", goToCheckoutScreen);
$("btn-reorder-all").addEventListener("click", reorderAll);

$("btn-remind-add-ai").addEventListener("click", async () => {
  await addAiToCart();
  hideAiRemindOverlay();
  showToast("AI pick added! Tap Place Order when ready.", "success");
});

$("btn-remind-checkout").addEventListener("click", finishCheckout);
$("btn-remind-back").addEventListener("click", hideAiRemindOverlay);

$("success-done").addEventListener("click", onSuccessContinue);

$("rating-stars").addEventListener("click", (e) => {
  const rating = parseInt(e.target.dataset.rating, 10);
  if (!rating) return;
  document.querySelectorAll("#rating-stars button").forEach((btn) => {
    btn.classList.toggle("active", parseInt(btn.dataset.rating, 10) <= rating);
  });
  onRatingComplete(rating);
});

$("skip-rating").addEventListener("click", onRatingSkip);

$("rating-overlay").addEventListener("click", (e) => {
  if (e.target === $("rating-overlay")) onRatingSkip();
});

$("ai-remind-overlay").addEventListener("click", (e) => {
  if (e.target === $("ai-remind-overlay")) hideAiRemindOverlay();
});

$("success-overlay").addEventListener("click", (e) => {
  if (e.target === $("success-overlay")) onSuccessContinue();
});

document.querySelectorAll(".habit-chip[data-pick]").forEach((chip) => {
  chip.addEventListener("click", () => {
    const pick = chip.dataset.pick;
    activePickFilter = activePickFilter === pick ? "all" : pick;
    document.querySelectorAll(".habit-chip[data-pick]").forEach((c) => {
      c.classList.toggle("active-filter", c.dataset.pick === activePickFilter);
    });
    renderQuickPicks();
  });
});

document.addEventListener("click", (e) => {
  const addBtn = e.target.closest("[data-add-id]");
  if (addBtn) {
    handleAddProduct(addBtn.dataset.addId);
    return;
  }
  const qtyBtn = e.target.closest("[data-qty-id]");
  if (qtyBtn) {
    changeQuantity(qtyBtn.dataset.qtyId, parseInt(qtyBtn.dataset.delta, 10));
  }
});

$("search-input").addEventListener("input", (e) => {
  searchQuery = e.target.value;
  renderSearchResults(searchProducts(searchQuery));
});

$("search-input").addEventListener("focus", () => {
  if (searchQuery.trim()) renderSearchResults(searchProducts(searchQuery));
});

$("search-clear").addEventListener("click", () => {
  closeSearch();
  $("search-input").focus();
});

$("search-backdrop").addEventListener("click", closeSearch);

loadSmartDiscovery().then(() => renderHome());
goToScreen("home");
