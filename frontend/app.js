/* ==============================================================================
   QuickBite — Client Application Core Engine
   Release: v2.0.0 End-Semester Laboratory Examination Release
============================================================================== */

const API_BASE = "/api";

class QuickBiteApp {
  constructor() {
    this.token = localStorage.getItem("quickbite_token") || null;
    this.currentUser = null;
    try {
      const stored = localStorage.getItem("quickbite_user");
      this.currentUser = stored ? JSON.parse(stored) : null;
    } catch (e) {
      this.currentUser = null;
    }

    this.activeRestaurantId = 1;
    this.restaurants = [];
    this.allMenuItems = [];
    this.currentCategoryFilter = "all";
    this.cart = { items: [], subtotal: 0.0 };
    this.activeOrder = null;
  }

  async init() {
    // Check if user is authenticated
    if (!this.token || !this.currentUser) {
      window.location.href = "/login";
      return;
    }

    // Verify token validity with backend
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: this.getAuthHeaders()
      });

      if (!res.ok) {
        // Expired or invalid token
        this.logout();
        return;
      }

      this.currentUser = await res.json();
      localStorage.setItem("quickbite_user", JSON.stringify(this.currentUser));
    } catch (err) {
      console.warn("Could not verify session with server, using local credentials", err);
    }

    // Render User Context in Navbar
    this.renderUserBadge();
    this.updateNavigationByRole();

    // Load initial data based on role
    if (this.currentUser.role === "customer") {
      await this.loadRestaurants();
      await this.loadCart();
      await this.loadCustomerOrders();
      this.showTab("browse");
    } else if (this.currentUser.role === "restaurant_staff") {
      await this.loadKitchenOrders();
      await this.loadStaffMenu();
      this.showTab("kitchen");
    } else if (this.currentUser.role === "admin") {
      await this.loadRestaurants();
      await this.loadAuditLogs();
      this.showTab("audit");
    }
  }

  getAuthHeaders() {
    const headers = { "Content-Type": "application/json" };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  renderUserBadge() {
    const nameEl = document.getElementById("current-user-name");
    const rolePill = document.getElementById("current-user-role-pill");

    if (nameEl && this.currentUser) {
      nameEl.textContent = this.currentUser.full_name;
    }

    if (rolePill && this.currentUser) {
      let roleLabel = "Customer";
      let roleClass = "role-customer";

      if (this.currentUser.role === "restaurant_staff") {
        roleLabel = `Staff (ID:${this.currentUser.restaurant_id || 1})`;
        roleClass = "role-staff";
      } else if (this.currentUser.role === "admin") {
        roleLabel = "Admin";
        roleClass = "role-admin";
      }

      rolePill.textContent = roleLabel;
      rolePill.className = `user-role-pill ${roleClass}`;
    }
  }

  updateNavigationByRole() {
    const role = this.currentUser ? this.currentUser.role : "customer";
    const isCustomer = role === "customer";
    const isStaff = role === "restaurant_staff";
    const isAdmin = role === "admin";

    // Nav buttons
    const btnBrowse = document.getElementById("btn-nav-browse");
    const btnOrders = document.getElementById("btn-nav-orders");
    const btnKitchen = document.getElementById("btn-nav-kitchen");
    const btnMenu = document.getElementById("btn-nav-menu");
    const btnAudit = document.getElementById("btn-nav-audit");
    const btnCart = document.getElementById("header-cart-btn");

    if (btnBrowse) btnBrowse.style.display = (isCustomer || isAdmin) ? "inline-block" : "none";
    if (btnOrders) btnOrders.style.display = (isCustomer || isAdmin) ? "inline-block" : "none";
    if (btnCart) btnCart.style.display = isCustomer ? "flex" : "none";

    if (btnKitchen) btnKitchen.style.display = (isStaff || isAdmin) ? "inline-block" : "none";
    if (btnMenu) btnMenu.style.display = (isStaff || isAdmin) ? "inline-block" : "none";
    if (btnAudit) btnAudit.style.display = isAdmin ? "inline-block" : "none";
  }

  handleAuthAction() {
    this.logout();
  }

  logout() {
    localStorage.removeItem("quickbite_token");
    localStorage.removeItem("quickbite_user");
    window.location.href = "/login";
  }

  showTab(tabName) {
    const tabs = ["browse", "cart", "orders", "kitchen", "menu-mgmt", "audit"];
    tabs.forEach(t => {
      const el = document.getElementById(`tab-${t}`);
      const btn = document.getElementById(`btn-nav-${t}`);
      if (el) el.classList.remove("active");
      if (btn) btn.classList.remove("active");
    });

    const activeEl = document.getElementById(`tab-${tabName}`);
    const activeBtn = document.getElementById(`btn-nav-${tabName}`);
    if (activeEl) activeEl.classList.add("active");
    if (activeBtn) activeBtn.classList.add("active");

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ============================================================================
  // RESTAURANTS & MENU BROWSING
  // ============================================================================

  async loadRestaurants() {
    try {
      const res = await fetch(`${API_BASE}/restaurants`, {
        headers: this.getAuthHeaders()
      });
      if (!res.ok) return;

      this.restaurants = await res.json();
      this.renderRestaurants();

      if (this.restaurants.length > 0) {
        this.selectRestaurant(this.restaurants[0].id);
      }
    } catch (e) {
      console.error("Error loading restaurants", e);
    }
  }

  renderRestaurants() {
    const container = document.getElementById("restaurants-container");
    if (!container) return;

    container.innerHTML = this.restaurants.map(r => `
      <div class="restaurant-card ${r.id === this.activeRestaurantId ? 'active-restaurant' : ''}" onclick="app.selectRestaurant(${r.id})">
        <div>
          <div class="rest-card-header">
            <h3 class="rest-card-name">${r.name}</h3>
            <span class="rest-cuisine-badge">${r.cuisine_type}</span>
          </div>
          <div class="rest-card-info">
            📍 ${r.address} • 📞 ${r.phone || 'Available'}
          </div>
        </div>
        <div class="rest-card-footer">
          <span class="active-indicator">
            <span class="active-dot"></span> Verified Kitchen
          </span>
          <span style="color: var(--primary); font-size: 0.78rem;">
            ${r.food_items ? r.food_items.length : 0} Specialties →
          </span>
        </div>
      </div>
    `).join("");
  }

  async selectRestaurant(restaurantId) {
    this.activeRestaurantId = restaurantId;
    this.renderRestaurants();

    const selected = this.restaurants.find(r => r.id === restaurantId);
    if (selected) {
      const titleEl = document.getElementById("selected-restaurant-title");
      const subEl = document.getElementById("selected-restaurant-subtitle");
      if (titleEl) titleEl.textContent = `${selected.name} — Menu`;
      if (subEl) subEl.textContent = `${selected.cuisine_type} Cuisine • Direct Kitchen Preparation`;
    }

    try {
      const res = await fetch(`${API_BASE}/restaurants/${restaurantId}/menu`, {
        headers: this.getAuthHeaders()
      });
      if (res.ok) {
        this.allMenuItems = await res.json();
        this.renderFoodItems();
      }
    } catch (e) {
      console.error("Error loading menu", e);
    }
  }

  filterCategory(category) {
    this.currentCategoryFilter = category;
    document.querySelectorAll(".filter-chip").forEach(chip => {
      if (chip.textContent.toLowerCase().includes(category.toLowerCase()) || 
          (category === 'all' && chip.textContent.includes('All'))) {
        chip.classList.add("active");
      } else {
        chip.classList.remove("active");
      }
    });
    this.renderFoodItems();
  }

  renderFoodItems() {
    const container = document.getElementById("food-items-container");
    const countEl = document.getElementById("menu-item-count");
    if (!container) return;

    let items = this.allMenuItems;
    if (this.currentCategoryFilter !== "all") {
      items = items.filter(i => i.category.toLowerCase() === this.currentCategoryFilter.toLowerCase());
    }

    if (countEl) {
      countEl.textContent = `${items.length} items available`;
    }

    if (items.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; padding: 3rem; text-align: center; color: var(--text-muted);">
          No dishes found for category '${this.currentCategoryFilter}'. Try selecting 'All Dishes'.
        </div>
      `;
      return;
    }

    container.innerHTML = items.map(item => `
      <div class="food-card">
        <div>
          <div class="food-header">
            <h4 class="food-title">${item.name}</h4>
            <span class="food-category-pill">${item.category}</span>
          </div>
          <p class="food-desc">${item.description || 'Prepared fresh using authentic ingredients.'}</p>
        </div>
        <div class="food-footer">
          <div>
            <span class="food-price">$${item.canonical_price.toFixed(2)}</span>
            <span class="food-price-subtext">Authoritative Price</span>
          </div>
          <button class="btn-add-cart" onclick="app.addToCart(${item.id})">
            + Add to Cart
          </button>
        </div>
      </div>
    `).join("");
  }

  // ============================================================================
  // CART & AUTHORITATIVE CHECKOUT
  // ============================================================================

  async loadCart() {
    try {
      const res = await fetch(`${API_BASE}/cart`, {
        headers: this.getAuthHeaders()
      });
      if (res.ok) {
        this.cart = await res.json();
        this.renderCart();
      }
    } catch (e) {
      console.error("Error loading cart", e);
    }
  }

  async addToCart(foodItemId) {
    try {
      const existing = this.cart.items.find(i => i.food_item_id === foodItemId);
      const newQty = existing ? existing.quantity + 1 : 1;

      const res = await fetch(`${API_BASE}/cart`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ food_item_id: foodItemId, quantity: newQty })
      });

      if (res.ok) {
        this.cart = await res.json();
        this.renderCart();
      }
    } catch (e) {
      console.error("Error adding to cart", e);
    }
  }

  async updateCartItemQty(foodItemId, quantity) {
    if (quantity <= 0) {
      await this.removeCartItem(foodItemId);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/cart`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ food_item_id: foodItemId, quantity: quantity })
      });

      if (res.ok) {
        this.cart = await res.json();
        this.renderCart();
      }
    } catch (e) {
      console.error("Error updating cart quantity", e);
    }
  }

  async removeCartItem(foodItemId) {
    try {
      const res = await fetch(`${API_BASE}/cart/items/${foodItemId}`, {
        method: "DELETE",
        headers: this.getAuthHeaders()
      });

      if (res.ok) {
        this.cart = await res.json();
        this.renderCart();
      }
    } catch (e) {
      console.error("Error removing cart item", e);
    }
  }

  async clearCart() {
    try {
      const res = await fetch(`${API_BASE}/cart`, {
        method: "DELETE",
        headers: this.getAuthHeaders()
      });

      if (res.ok) {
        this.cart = await res.json();
        this.renderCart();
      }
    } catch (e) {
      console.error("Error clearing cart", e);
    }
  }

  renderCart() {
    const listEl = document.getElementById("cart-items-list");
    const emptyMsg = document.getElementById("cart-empty-message");
    const countBadge = document.getElementById("cart-counter");

    const totalCount = this.cart.items.reduce((sum, i) => sum + i.quantity, 0);
    if (countBadge) countBadge.textContent = totalCount;

    if (!listEl) return;

    if (!this.cart.items || this.cart.items.length === 0) {
      listEl.innerHTML = "";
      if (emptyMsg) emptyMsg.style.display = "block";
      this.updateCheckoutTotals(0.0);
      return;
    }

    if (emptyMsg) emptyMsg.style.display = "none";

    listEl.innerHTML = this.cart.items.map(item => `
      <div class="cart-line-item">
        <div class="item-details">
          <div class="item-name">${item.food_item_name}</div>
          <div class="item-unit-price">$${item.unit_price.toFixed(2)} each</div>
        </div>
        <div class="qty-controls">
          <button class="qty-btn" onclick="app.updateCartItemQty(${item.food_item_id}, ${item.quantity - 1})">-</button>
          <span class="qty-num">${item.quantity}</span>
          <button class="qty-btn" onclick="app.updateCartItemQty(${item.food_item_id}, ${item.quantity + 1})">+</button>
        </div>
        <div style="font-weight: 750; min-width: 65px; text-align: right;">
          $${item.line_total.toFixed(2)}
        </div>
        <button class="btn-secondary" style="padding: 2px 7px; margin-left: 0.5rem; font-size: 0.75rem;" onclick="app.removeCartItem(${item.food_item_id})">✕</button>
      </div>
    `).join("");

    this.updateCheckoutTotals(this.cart.subtotal);
  }

  updateCheckoutTotals(subtotal) {
    const subtotalEl = document.getElementById("cart-subtotal");
    const taxEl = document.getElementById("cart-tax");
    const grandTotalEl = document.getElementById("cart-grand-total");

    const tax = roundToTwo(subtotal * 0.10);
    const delivery = subtotal > 0 ? 3.00 : 0.0;
    const grand = roundToTwo(subtotal + tax + delivery);

    if (subtotalEl) subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
    if (taxEl) taxEl.textContent = `$${tax.toFixed(2)}`;
    if (grandTotalEl) grandTotalEl.textContent = `$${grand.toFixed(2)}`;
  }

  async submitOrder() {
    if (!this.cart.items || this.cart.items.length === 0) {
      alert("Your cart is empty. Please add items before checking out.");
      return;
    }

    const address = document.getElementById("checkout-address").value.trim();
    const paymentToken = document.getElementById("checkout-payment-token").value;
    const btn = document.getElementById("btn-submit-order");

    if (!address || address.length < 5) {
      alert("Please provide a valid delivery street address (minimum 5 characters).");
      return;
    }

    btn.disabled = true;
    btn.textContent = "Processing Authoritative Order...";

    try {
      const payload = {
        restaurant_id: this.activeRestaurantId,
        items: this.cart.items.map(i => ({
          food_item_id: i.food_item_id,
          quantity: i.quantity
        })),
        delivery_address: address,
        payment_token: paymentToken
      };

      const res = await fetch(`${API_BASE}/orders`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        alert(`Order processing declined: ${data.detail || "Transaction failed"}`);
        btn.disabled = false;
        btn.textContent = "Place Secure Order Now";
        return;
      }

      alert(`Order #${data.id} successfully created and confirmed! Server computed total: $${data.total_amount.toFixed(2)}.`);

      await this.loadCart();
      await this.loadCustomerOrders();
      this.showTab("orders");

    } catch (e) {
      console.error("Order submission error", e);
      alert("A network error occurred while submitting order.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Place Secure Order Now";
    }
  }

  // ============================================================================
  // CUSTOMER ORDER HISTORY & LIVE TIMELINE TRACKING
  // ============================================================================

  async loadCustomerOrders() {
    try {
      const res = await fetch(`${API_BASE}/orders`, {
        headers: this.getAuthHeaders()
      });
      if (!res.ok) return;

      const orders = await res.json();
      this.renderCustomerOrders(orders);

      if (orders.length > 0) {
        this.activeOrder = orders[0];
        this.renderLiveTracking(orders[0]);
      } else {
        const panel = document.getElementById("live-tracking-panel");
        if (panel) panel.style.display = "none";
      }
    } catch (e) {
      console.error("Error loading customer orders", e);
    }
  }

  renderCustomerOrders(orders) {
    const tbody = document.getElementById("orders-table-body");
    if (!tbody) return;

    if (orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No previous orders found.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => {
      const dateStr = new Date(o.created_at).toLocaleString();
      const itemsStr = o.items ? o.items.map(i => `${i.quantity}x ${i.food_item_name}`).join(", ") : "Items";
      const statusClass = `badge-${o.status.toLowerCase()}`;

      return `
        <tr>
          <td><strong>#${o.id}</strong></td>
          <td style="font-size: 0.8rem; color: var(--text-secondary);">${dateStr}</td>
          <td>${o.restaurant_name || `Restaurant #${o.restaurant_id}`}</td>
          <td style="max-width: 250px; font-size: 0.82rem;">${itemsStr}</td>
          <td><strong>$${o.total_amount.toFixed(2)}</strong></td>
          <td><span class="badge ${statusClass}">${o.status}</span></td>
          <td>
            <button class="btn-secondary" style="font-size: 0.78rem; padding: 3px 8px;" onclick="app.viewOrderDetails(${o.id})">
              Track
            </button>
            ${o.status === 'PLACED' ? `
              <button class="btn-danger" style="font-size: 0.78rem; padding: 3px 8px; margin-left: 4px;" onclick="app.cancelOrderById(${o.id})">
                Cancel
              </button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join("");
  }

  viewOrderDetails(orderId) {
    fetch(`${API_BASE}/orders/${orderId}`, {
      headers: this.getAuthHeaders()
    }).then(r => r.json()).then(order => {
      this.activeOrder = order;
      this.renderLiveTracking(order);
      window.scrollTo({ top: 150, behavior: "smooth" });
    });
  }

  renderLiveTracking(order) {
    const panel = document.getElementById("live-tracking-panel");
    if (!panel) return;

    panel.style.display = "block";
    document.getElementById("track-order-id").textContent = order.id;
    document.getElementById("track-restaurant-name").textContent = order.restaurant_name || `Kitchen #${order.restaurant_id}`;

    const badge = document.getElementById("track-status-badge");
    badge.textContent = order.status;
    badge.className = `badge badge-${order.status.toLowerCase()}`;

    const cancelBtn = document.getElementById("track-cancel-btn");
    if (cancelBtn) {
      cancelBtn.style.display = order.status === "PLACED" ? "inline-block" : "none";
    }

    const steps = ["placed", "accepted", "preparing", "out_for_delivery", "delivered"];
    const statusOrder = {
      "PLACED": 0,
      "ACCEPTED": 1,
      "PREPARING": 2,
      "OUT_FOR_DELIVERY": 3,
      "DELIVERED": 4,
      "CANCELLED": -1,
      "REJECTED": -1
    };

    const currentIdx = statusOrder[order.status] ?? 0;

    steps.forEach((st, idx) => {
      const node = document.getElementById(`step-node-${st}`);
      if (!node) return;

      node.classList.remove("active", "completed");
      if (currentIdx === -1) {
        // Cancelled or rejected
      } else if (idx < currentIdx) {
        node.classList.add("completed");
        node.textContent = "✓";
      } else if (idx === currentIdx) {
        node.classList.add("active");
        node.textContent = (idx + 1).toString();
      } else {
        node.textContent = (idx + 1).toString();
      }
    });
  }

  async cancelActiveOrder() {
    if (!this.activeOrder) return;
    await this.cancelOrderById(this.activeOrder.id);
  }

  async cancelOrderById(orderId) {
    if (!confirm(`Are you sure you want to cancel Order #${orderId}? Cancellation is allowed strictly prior to kitchen acceptance.`)) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/cancel`, {
        method: "POST",
        headers: this.getAuthHeaders()
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Cannot cancel order: ${data.detail || "State invariant rejected"}`);
        return;
      }

      alert(`Order #${orderId} has been successfully cancelled and refund initiated.`);
      await this.loadCustomerOrders();
    } catch (e) {
      console.error("Cancellation error", e);
    }
  }

  // ============================================================================
  // RESTAURANT STAFF: KITCHEN DASHBOARD & FSM PROGRESSION
  // ============================================================================

  async loadKitchenOrders() {
    try {
      const res = await fetch(`${API_BASE}/orders/kitchen`, {
        headers: this.getAuthHeaders()
      });

      if (!res.ok) {
        const err = await res.json();
        console.warn("Could not load kitchen queue", err);
        return;
      }

      const orders = await res.json();
      this.renderKitchenOrders(orders);
    } catch (e) {
      console.error("Error loading kitchen orders", e);
    }
  }

  renderKitchenOrders(orders) {
    const tbody = document.getElementById("kitchen-table-body");
    const restNameHeader = document.getElementById("kitchen-restaurant-name");
    if (!tbody) return;

    if (restNameHeader && orders.length > 0) {
      restNameHeader.textContent = orders[0].restaurant_name || `Restaurant #${orders[0].restaurant_id}`;
    }

    if (orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">No incoming kitchen orders at this time.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => {
      const timeStr = new Date(o.created_at).toLocaleTimeString();
      const dishesStr = o.items ? o.items.map(i => `<strong>${i.quantity}x</strong> ${i.food_item_name}`).join("<br>") : "-";
      const statusClass = `badge-${o.status.toLowerCase()}`;

      let actionsHtml = "";
      if (o.status === "PLACED") {
        actionsHtml = `
          <button class="btn-primary" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.updateOrderStatus(${o.id}, 'ACCEPTED')">Accept</button>
          <button class="btn-danger" style="font-size: 0.75rem; padding: 3px 8px; margin-left: 4px;" onclick="app.updateOrderStatus(${o.id}, 'REJECTED')">Reject</button>
        `;
      } else if (o.status === "ACCEPTED") {
        actionsHtml = `
          <button class="btn-primary" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.updateOrderStatus(${o.id}, 'PREPARING')">Cook / Prepare</button>
        `;
      } else if (o.status === "PREPARING") {
        actionsHtml = `
          <button class="btn-primary" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.updateOrderStatus(${o.id}, 'OUT_FOR_DELIVERY')">Dispatch</button>
        `;
      } else if (o.status === "OUT_FOR_DELIVERY") {
        actionsHtml = `
          <button class="btn-primary" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.updateOrderStatus(${o.id}, 'DELIVERED')">Complete</button>
        `;
      } else {
        actionsHtml = `<span style="font-size: 0.75rem; color: var(--text-muted);">Terminal State</span>`;
      }

      return `
        <tr>
          <td><strong>#${o.id}</strong></td>
          <td style="font-size: 0.8rem; color: var(--text-secondary);">${timeStr}</td>
          <td>${o.customer_name || `User #${o.customer_id}`}</td>
          <td style="font-size: 0.82rem; max-width: 180px;">${o.delivery_address}</td>
          <td style="font-size: 0.82rem;">${dishesStr}</td>
          <td><strong>$${o.total_amount.toFixed(2)}</strong></td>
          <td><span class="badge ${statusClass}">${o.status}</span></td>
          <td>${actionsHtml}</td>
        </tr>
      `;
    }).join("");
  }

  async updateOrderStatus(orderId, nextStatus) {
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/status`, {
        method: "PATCH",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ status: nextStatus })
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`State transition failed: ${data.detail || "FSM violation"}`);
        return;
      }

      await this.loadKitchenOrders();
    } catch (e) {
      console.error("Error updating order status", e);
    }
  }

  // ============================================================================
  // RESTAURANT STAFF: MENU MANAGEMENT
  // ============================================================================

  async loadStaffMenu() {
    const restId = this.currentUser.restaurant_id || 1;
    try {
      const res = await fetch(`${API_BASE}/restaurants/${restId}/menu`, {
        headers: this.getAuthHeaders()
      });
      if (!res.ok) return;

      const items = await res.json();
      this.renderStaffMenu(items);
    } catch (e) {
      console.error("Error loading staff menu", e);
    }
  }

  renderStaffMenu(items) {
    const tbody = document.getElementById("staff-menu-table-body");
    if (!tbody) return;

    tbody.innerHTML = items.map(i => `
      <tr>
        <td><strong>#${i.id}</strong></td>
        <td><strong>${i.name}</strong><br><small style="color:var(--text-muted);">${i.description || ''}</small></td>
        <td><span class="food-category-pill">${i.category}</span></td>
        <td><strong>$${i.canonical_price.toFixed(2)}</strong></td>
        <td>${i.is_available ? '<span class="active-indicator"><span class="active-dot"></span> Available</span>' : '<span style="color:var(--danger)">Unavailable</span>'}</td>
        <td>
          <button class="btn-secondary" style="font-size: 0.75rem; padding: 2px 8px;" onclick="app.toggleItemAvailability(${i.id}, ${!i.is_available})">
            ${i.is_available ? 'Make Unavailable' : 'Make Available'}
          </button>
        </td>
      </tr>
    `).join("");
  }

  async toggleItemAvailability(itemId, newStatus) {
    const restId = this.currentUser.restaurant_id || 1;
    try {
      const res = await fetch(`${API_BASE}/restaurants/${restId}/menu/${itemId}`, {
        method: "PATCH",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ is_available: newStatus })
      });
      if (res.ok) {
        await this.loadStaffMenu();
      }
    } catch (e) {
      console.error("Error toggling item", e);
    }
  }

  openAddDishModal() {
    document.getElementById("dish-modal").style.display = "flex";
  }

  closeDishModal() {
    document.getElementById("dish-modal").style.display = "none";
  }

  async handleCreateDishSubmit(event) {
    event.preventDefault();
    const restId = this.currentUser.restaurant_id || 1;
    const name = document.getElementById("dish-name").value.trim();
    const desc = document.getElementById("dish-desc").value.trim();
    const price = parseFloat(document.getElementById("dish-price").value);
    const category = document.getElementById("dish-category").value.trim() || "General";

    if (!name || isNaN(price) || price <= 0) {
      alert("Please provide a valid dish name and positive price.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/restaurants/${restId}/menu`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          name: name,
          description: desc,
          canonical_price: price,
          category: category,
          is_available: true
        })
      });

      if (res.ok) {
        this.closeDishModal();
        alert(`Food item '${name}' published to canonical menu!`);
        await this.loadStaffMenu();
      } else {
        const err = await res.json();
        alert(`Error adding dish: ${err.detail || "Server error"}`);
      }
    } catch (e) {
      console.error("Error creating dish", e);
    }
  }

  // ============================================================================
  // ADMIN: TAMPER-EVIDENT AUDIT LEDGER
  // ============================================================================

  async loadAuditLogs() {
    try {
      const res = await fetch(`${API_BASE}/audit/logs?limit=50`, {
        headers: this.getAuthHeaders()
      });

      if (!res.ok) {
        console.warn("Could not load audit logs. Requires Admin privilege.");
        return;
      }

      const logs = await res.json();
      this.renderAuditLogs(logs);
    } catch (e) {
      console.error("Error loading audit logs", e);
    }
  }

  renderAuditLogs(logs) {
    const tbody = document.getElementById("audit-table-body");
    if (!tbody) return;

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No audit records available.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const dateStr = new Date(l.created_at).toLocaleString();
      const statusColor = l.status_result === "SUCCESS" ? "var(--secondary)" : "var(--danger)";

      return `
        <tr>
          <td style="font-size: 0.78rem; color: var(--text-secondary);">${dateStr}</td>
          <td><code style="background:var(--bg-subtle); padding: 2px 6px; border-radius: 4px; font-weight: 700;">${l.action_type}</code></td>
          <td>${l.user_id ? `User #${l.user_id}` : 'Anonymous / System'}</td>
          <td>${l.entity_name}</td>
          <td><strong style="color: ${statusColor};">${l.status_result}</strong></td>
          <td style="font-size: 0.8rem; font-family: monospace;">${l.client_ip || 'local'}</td>
          <td style="font-size: 0.8rem; max-width: 280px; word-break: break-all;">${l.details_json || '-'}</td>
        </tr>
      `;
    }).join("");
  }

  // ============================================================================
  // SECURITY POSTURE DASHBOARD MODAL
  // ============================================================================

  openSecurityModal() {
    const modal = document.getElementById("security-modal");
    if (modal) modal.style.display = "flex";
  }

  closeSecurityModal() {
    const modal = document.getElementById("security-modal");
    if (modal) modal.style.display = "none";
  }
}

function roundToTwo(num) {
  return +(Math.round(num + "e+2") + "e-2");
}

// Global App Instance Initializer
const app = new QuickBiteApp();
window.addEventListener("DOMContentLoaded", () => {
  app.init();
});
