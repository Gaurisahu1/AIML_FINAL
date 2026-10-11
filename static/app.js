/**
 * ShopEasy Smart Notifications - Interactive Dashboard Client
 * Vanilla JavaScript, Zero External Dependencies, Offline-Ready
 */

(function () {
  "use strict";

  // Application State Cache
  let appState = {
    customers: [],
    selectedCustomer: null,
    systemRun: false,
    summaryMetrics: {},
    standardBundle: [],
    activeTab: "tab-simulate",
    roleHintsVisible: false,
    compareWithBefore: false,
    autoDemoRunning: false,
    autoDemoPaused: false,
    autoDemoTimer: null,
    autoDemoStep: 0,
    tab2Subview: "inboxes",
    demoTime: "afternoon",
    composeState: {
      customerId: "aarav",
      type: "offer",
      category: "Fashion",
      item: "Sneakers",
      highlight: "20% off",
      urgency: "normal",
      isSubmitting: false,
      lastEvaluatedItem: null
    },
    activeModal: null
  };

  // DOM Elements Cache
  const dom = {
    tabBtns: document.querySelectorAll(".tab-btn"),
    tabPanels: document.querySelectorAll(".tab-panel"),
    themeToggleBtn: document.getElementById("theme-toggle-btn"),
    resetBtn: document.getElementById("reset-btn"),
    resetModal: document.getElementById("reset-modal"),
    resetCancelBtn: document.getElementById("reset-cancel-btn"),
    resetConfirmBtn: document.getElementById("reset-confirm-btn"),
    autoDemoBtn: document.getElementById("auto-demo-btn"),
    demoController: document.getElementById("demo-controller"),
    demoProgressFill: document.getElementById("demo-progress-fill"),
    demoStatusText: document.getElementById("demo-status-text"),
    demoPauseBtn: document.getElementById("demo-pause-btn"),
    demoStopBtn: document.getElementById("demo-stop-btn"),
    loadingOverlay: document.getElementById("loading-overlay"),
    
    // Tab 1 Elements
    roleHintsToggle: document.getElementById("role-hints-toggle"),
    customerCardsContainer: document.getElementById("customer-cards-container"),
    playCustomerBtn: document.getElementById("play-customer-btn"),
    loadSampleBtn: document.getElementById("load-sample-btn"),
    phoneAvatar: document.getElementById("phone-avatar"),
    phoneCustName: document.getElementById("phone-cust-name"),
    phoneCustSub: document.getElementById("phone-cust-sub"),
    phoneWeekBadge: document.getElementById("phone-week-badge"),
    simNotifsStream: document.getElementById("sim-notifs-stream"),
    submitWeekBtn: document.getElementById("submit-week-btn"),
    submitHelpText: document.getElementById("submit-help-text"),
    runSystemBanner: document.getElementById("run-system-banner"),
    runSystemBtn: document.getElementById("run-system-btn"),
    
    // Tab 2 Elements
    compareToggle: document.getElementById("compare-toggle"),
    notifCustList: document.getElementById("notif-cust-list"),
    outPhoneAvatar: document.getElementById("out-phone-avatar"),
    outPhoneName: document.getElementById("out-phone-name"),
    outPhoneCount: document.getElementById("out-phone-count"),
    outStatusPill: document.getElementById("out-status-pill"),
    outNotifsStream: document.getElementById("out-notifs-stream"),
    continueCustomerBtn: document.getElementById("continue-customer-btn"),
    continuedDrawer: document.getElementById("continued-drawer"),
    contCustName: document.getElementById("cont-cust-name"),
    contNotifsStream: document.getElementById("cont-notifs-stream"),
    contSubmitBtn: document.getElementById("cont-submit-btn"),
    contCancelBtn: document.getElementById("cont-cancel-btn"),

    // Tab 2 Segmented Control & Compose Elements
    segInboxesBtn: document.getElementById("seg-inboxes-btn"),
    segComposeBtn: document.getElementById("seg-compose-btn"),
    subviewInboxes: document.getElementById("subview-inboxes"),
    subviewCompose: document.getElementById("subview-compose"),
    composePrereqBanner: document.getElementById("compose-prereq-banner"),
    composeActiveLayout: document.getElementById("compose-active-layout"),
    composeGoSimBtn: document.getElementById("compose-go-sim-btn"),
    composeCustomerSelect: document.getElementById("compose-customer-select"),
    composeCustHintText: document.getElementById("compose-cust-hint-text"),
    composeTypeChips: document.getElementById("compose-type-chips"),
    composeCategoryChips: document.getElementById("compose-category-chips"),
    composeItemSelect: document.getElementById("compose-item-select"),
    composeHighlightSelect: document.getElementById("compose-highlight-select"),
    composeUrgencyChips: document.getElementById("compose-urgency-chips"),
    composeEssentialNote: document.getElementById("compose-essential-note"),
    composeGenerateBtn: document.getElementById("compose-generate-btn"),
    demoTimeSelector: document.getElementById("demo-time-selector"),
    compPhoneAvatar: document.getElementById("comp-phone-avatar"),
    compPhoneName: document.getElementById("comp-phone-name"),
    compPhoneCount: document.getElementById("comp-phone-count"),
    compStatusPill: document.getElementById("comp-status-pill"),
    compNotifsStream: document.getElementById("comp-notifs-stream"),
    recActCustName: document.getElementById("rec-act-cust-name"),
    recentActivityList: document.getElementById("recent-activity-list"),

    // Modals & Toasts
    modalScheduled: document.getElementById("modal-scheduled"),
    modalSchedCust: document.getElementById("modal-sched-cust"),
    modalSchedTime: document.getElementById("modal-sched-time"),
    modalSchedReason: document.getElementById("modal-sched-reason"),
    modalSchedPreview: document.getElementById("modal-sched-preview"),
    modalSchedCancelBtn: document.getElementById("modal-sched-cancel-btn"),
    modalSchedOverrideBtn: document.getElementById("modal-sched-override-btn"),
    modalSchedOkBtn: document.getElementById("modal-sched-ok-btn"),

    modalNotSent: document.getElementById("modal-not-sent"),
    modalNotSentCust: document.getElementById("modal-not-sent-cust"),
    modalNotSentReason: document.getElementById("modal-not-sent-reason"),
    modalNotSentPreview: document.getElementById("modal-not-sent-preview"),
    modalNotSentOverrideBtn: document.getElementById("modal-not-sent-override-btn"),
    modalNotSentOkBtn: document.getElementById("modal-not-sent-ok-btn"),

    modalConfirmOverride: document.getElementById("modal-confirm-override"),
    modalConfirmCancelBtn: document.getElementById("modal-confirm-cancel-btn"),
    modalConfirmProceedBtn: document.getElementById("modal-confirm-proceed-btn"),

    toastContainer: document.getElementById("toast-container"),
    
    // Tab 3 Elements
    metricEngaged: document.getElementById("metric-engaged"),
    metricLosing: document.getElementById("metric-losing"),
    metricRisk: document.getElementById("metric-risk"),
    metricUnsub: document.getElementById("metric-unsub"),
    metricAvoided: document.getElementById("metric-avoided"),
    insightsCustList: document.getElementById("insights-cust-list"),
    insAvatar: document.getElementById("ins-avatar"),
    insName: document.getElementById("ins-name"),
    insTopInterest: document.getElementById("ins-top-interest"),
    insStatusBadge: document.getElementById("ins-status-badge"),
    insInterestsList: document.getElementById("ins-interests-list"),
    insChartContainer: document.getElementById("ins-chart-container"),
    insTrendBadge: document.getElementById("ins-trend-badge"),
    insRiskBadge: document.getElementById("ins-risk-badge"),
    insLikelyBehavior: document.getElementById("ins-likely-behavior"),
    insObservationsList: document.getElementById("ins-observations-list"),
    insFrequencyLine: document.getElementById("ins-frequency-line"),
    insDecisionsContainer: document.getElementById("ins-decisions-container"),
    insRecActionTitle: document.getElementById("ins-rec-action-title"),
    insRecActionDesc: document.getElementById("ins-rec-action-desc")
  };

  const COMPOSE_CATEGORY_ITEMS = {
    "Fashion": ["Sneakers", "Denim jacket", "Handbag", "Watch"],
    "Electronics": ["Wireless headphones", "Smartwatch", "Power bank", "Bluetooth speaker"],
    "Home & Kitchen": ["Air fryer", "Bedsheet set", "Cookware set", "Table lamp"],
    "Beauty": ["Face serum", "Perfume", "Sunscreen", "Lipstick set"],
    "Groceries": ["Fresh fruits box", "Snack combo", "Organic staples", "Coffee beans"],
    "Sports": ["Running shoes", "Yoga mat", "Cricket bat", "Gym gloves"]
  };

  const COMPOSE_TYPE_HIGHLIGHTS = {
    "offer": ["20% off", "40% off", "Buy 1 Get 1", "Free delivery"],
    "new_arrival": ["Just launched", "Back in stock", "Limited edition", "Trending now"],
    "price_drop": ["Price just dropped", "Lowest this month", "Only a few left"],
    "order_update": ["Shipped", "Out for delivery", "Delivered", "Delayed"]
  };

  // SVGs for categories
  const CATEGORY_ICONS = {
    offer: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>`,
    new_arrival: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
    price_drop: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>`,
    order_update: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`
  };

  const CATEGORY_NAMES = {
    offer: "Offers & Sales",
    new_arrival: "New Arrivals",
    price_drop: "Price Drops",
    order_update: "Order Updates"
  };

  // =========================================================================
  // INITIALIZATION
  // =========================================================================

  async function init() {
    setupTheme();
    setupEventListeners();
    await fetchState();
  }

  function setupTheme() {
    const saved = localStorage.getItem("shopeasy_theme") || "light";
    document.documentElement.setAttribute("data-theme", saved);
  }

  function toggleTheme() {
    const cur = document.documentElement.getAttribute("data-theme") || "light";
    const next = cur === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("shopeasy_theme", next);
  }

  // =========================================================================
  // STATE MANAGEMENT & API CALLS
  // =========================================================================

  async function fetchState() {
    try {
      const res = await fetch("/api/state");
      const data = await res.json();
      appState.customers = data.customers;
      appState.selectedCustomer = data.selected_customer;
      appState.systemRun = data.system_run;
      appState.summaryMetrics = data.summary_metrics;
      appState.standardBundle = data.standard_bundle;

      renderAll();
    } catch (err) {
      console.error("Failed to fetch state:", err);
    }
  }

  async function selectCustomer(cid) {
    try {
      await fetch(`/api/customer/${cid}/select`, { method: "POST" });
      await fetchState();
    } catch (err) {
      console.error("Failed to select customer:", err);
    }
  }

  async function submitWeekActions(cid, actions) {
    try {
      await fetch(`/api/customer/${cid}/submit-week`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ actions })
      });
      await fetchState();
    } catch (err) {
      console.error("Failed to submit week:", err);
    }
  }

  async function autoPlayCustomer(cid) {
    try {
      await fetch(`/api/customer/${cid}/auto-play`, { method: "POST" });
      await fetchState();
    } catch (err) {
      console.error("Failed to auto-play customer:", err);
    }
  }

  async function loadSampleBehaviour() {
    try {
      await fetch("/api/sample-behaviour", { method: "POST" });
      await fetchState();
    } catch (err) {
      console.error("Failed to load sample behaviour:", err);
    }
  }

  async function runSystem() {
    // Show friendly loading overlay for ~2 seconds
    dom.loadingOverlay.classList.remove("hidden");
    await new Promise((r) => setTimeout(r, 1800));

    try {
      await fetch("/api/run-system", { method: "POST" });
      await fetchState();
    } catch (err) {
      console.error("Failed to run system:", err);
    } finally {
      dom.loadingOverlay.classList.add("hidden");
      switchTab("tab-notifications");
    }
  }

  async function resetDemo() {
    try {
      await fetch("/api/reset", { method: "POST" });
      dom.resetModal.classList.add("hidden");
      for (const k in cachedRecentActivity) delete cachedRecentActivity[k];
      appState.demoTime = "afternoon";
      appState.composeState.lastEvaluatedItem = null;
      await fetchState();
      switchTab("tab-simulate");
    } catch (err) {
      console.error("Failed to reset:", err);
    }
  }

  // =========================================================================
  // TAB NAVIGATION & SHORTCUTS
  // =========================================================================

  function switchTab(tabId) {
    appState.activeTab = tabId;
    dom.tabBtns.forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
    });
    dom.tabPanels.forEach((panel) => {
      panel.classList.toggle("active", panel.id === tabId);
    });

    // Close continued drawer when switching tabs
    dom.continuedDrawer.classList.add("hidden");
  }

  function handleKeyboardNav(e) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    if (e.key === "Escape") {
      if (appState.activeModal) {
        closeModal(appState.activeModal);
      }
      dom.resetModal.classList.add("hidden");
      dom.continuedDrawer.classList.add("hidden");
      return;
    }

    if (e.key === "ArrowRight") {
      if (appState.activeTab === "tab-simulate") switchTab("tab-notifications");
      else if (appState.activeTab === "tab-notifications") switchTab("tab-insights");
    } else if (e.key === "ArrowLeft") {
      if (appState.activeTab === "tab-insights") switchTab("tab-notifications");
      else if (appState.activeTab === "tab-notifications") switchTab("tab-simulate");
    } else if (e.key === "r" || e.key === "R") {
      dom.resetModal.classList.remove("hidden");
    }
  }

  // =========================================================================
  // RENDERING
  // =========================================================================

  function renderAll() {
    renderTab1();
    renderTab2();
    renderTab3();
  }

  // --- TAB 1: Simulate Customers ---
  function renderTab1() {
    const custs = appState.customers;
    const sel = appState.selectedCustomer;
    if (!sel) return;

    // 1. Render Customer Cards Grid
    dom.customerCardsContainer.innerHTML = custs
      .map((c) => {
        const isSelected = c.id === sel.id;
        const isCompleted = c.is_finished;
        const isUnsub = c.is_unsubscribed;

        let badgeClass = "progress-pill";
        let badgeText = `Week ${c.current_week} of 5`;
        if (isUnsub) {
          badgeClass += " unsubscribed";
          badgeText = "Unsubscribed";
        } else if (isCompleted) {
          badgeClass += " completed";
          badgeText = "Finished ✓";
        }

        const roleVisibleClass = appState.roleHintsVisible ? "visible" : "";

        return `
          <div class="cust-card ${isSelected ? "selected" : ""}" data-cid="${c.id}">
            <div class="cust-card-top">
              <div class="avatar">${c.initials}</div>
              <span class="${badgeClass}">${badgeText}</span>
            </div>
            <div class="cust-card-info">
              <span class="cust-name">${c.name}</span>
              <span class="cust-role-hint ${roleVisibleClass}">${c.role_hint}</span>
            </div>
          </div>
        `;
      })
      .join("");

    // Add click listeners to cards
    dom.customerCardsContainer.querySelectorAll(".cust-card").forEach((card) => {
      card.addEventListener("click", () => {
        selectCustomer(card.getAttribute("data-cid"));
      });
    });

    // 2. Render Phone Mockup for Selected Customer
    dom.phoneAvatar.textContent = sel.initials;
    dom.phoneCustName.textContent = sel.name;

    if (sel.is_unsubscribed) {
      dom.phoneCustSub.textContent = "Customer unsubscribed from all alerts";
      dom.phoneWeekBadge.textContent = "Ended";
      dom.simNotifsStream.innerHTML = `
        <div class="empty-phone-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
          </svg>
          <div class="empty-phone-title">Customer Unsubscribed</div>
          <p>No further alerts sent.</p>
        </div>
      `;
      dom.submitWeekBtn.disabled = true;
      dom.submitHelpText.textContent = "Simulation completed for this customer";
    } else if (sel.is_finished) {
      dom.phoneCustSub.textContent = "Completed all 5 simulation weeks";
      dom.phoneWeekBadge.textContent = "Week 5 ✓";
      dom.simNotifsStream.innerHTML = `
        <div class="empty-phone-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <div class="empty-phone-title">All 5 Weeks Complete</div>
          <p>Ready to run the system or inspect other customers.</p>
        </div>
      `;
      dom.submitWeekBtn.disabled = true;
      dom.submitHelpText.textContent = "All weeks submitted";
    } else {
      dom.phoneCustSub.textContent = `Week ${sel.current_week} of 5 • 6 alerts to review`;
      dom.phoneWeekBadge.textContent = `Week ${sel.current_week}`;

      const notifs = sel.active_week_notifications || [];
      dom.simNotifsStream.innerHTML = notifs
        .map((n, idx) => {
          const act = n.action;
          const isDone = !!act;
          const isOpened = act === "opened";
          const dur = n.duration || "few_seconds";
          const timing = n.timing || "right_away";

          return `
            <div class="sim-notif-card ${isDone ? "completed-action" : ""}" data-nid="${n.id}">
              <div class="sim-notif-top">
                <span class="category-tag ${n.type}">
                  ${CATEGORY_ICONS[n.type]}
                  <span>${CATEGORY_NAMES[n.type]}</span>
                </span>
                <span class="notif-time">${n.day_name}, ${n.time}</span>
              </div>
              <div class="sim-notif-text">${n.text}</div>
              
              <!-- Primary Actions Group -->
              <div class="action-buttons-group">
                <button type="button" class="act-btn ${act === "opened" ? "active" : ""}" data-act="opened">Open</button>
                <button type="button" class="act-btn ${act === "ignored" ? "active" : ""}" data-act="ignored">Ignore</button>
                <button type="button" class="act-btn ${act === "dismissed" ? "active" : ""}" data-act="dismissed">Dismiss</button>
                <button type="button" class="act-btn danger ${act === "muted" ? "active" : ""}" data-act="muted">Mute</button>
                <button type="button" class="act-btn danger ${act === "unsubscribed" ? "active" : ""}" data-act="unsubscribed">Unsubscribe</button>
              </div>

              <!-- Open Sub-options Accordion -->
              ${
                isOpened
                  ? `
                <div class="open-details-panel">
                  <div class="open-row">
                    <span class="open-label">How long:</span>
                    <div class="pill-group">
                      <button type="button" class="pill-opt ${dur === "quick_glance" ? "active" : ""}" data-dur="quick_glance">Quick glance</button>
                      <button type="button" class="pill-opt ${dur === "few_seconds" ? "active" : ""}" data-dur="few_seconds">A few seconds</button>
                      <button type="button" class="pill-opt ${dur === "read_fully" ? "active" : ""}" data-dur="read_fully">Read fully</button>
                    </div>
                  </div>
                  <div class="open-row">
                    <span class="open-label">Responded:</span>
                    <div class="pill-group">
                      <button type="button" class="pill-opt ${timing === "right_away" ? "active" : ""}" data-time="right_away">Right away</button>
                      <button type="button" class="pill-opt ${timing === "later_today" ? "active" : ""}" data-time="later_today">Later today</button>
                      <button type="button" class="pill-opt ${timing === "next_day" ? "active" : ""}" data-time="next_day">Next day</button>
                    </div>
                  </div>
                  <div class="toggle-opt-row">
                    <label class="chk-chip">
                      <input type="checkbox" class="chk-tapped" ${n.clicked ? "checked" : ""}>
                      <span>Tapped through to product</span>
                    </label>
                    <label class="chk-chip">
                      <input type="checkbox" class="chk-saved" ${n.saved ? "checked" : ""}>
                      <span>Saved for later</span>
                    </label>
                  </div>
                </div>
              `
                  : ""
              }
            </div>
          `;
        })
        .join("");

      // Add interactive event listeners inside phone cards
      attachPhoneStreamListeners(sel);
      validateSubmitButton(sel);
    }

    // 3. Check if all active customers are finished -> reveal Run System Banner
    const allFinished = custs.filter((c) => c.id !== "guest").every((c) => c.is_finished);
    dom.runSystemBanner.classList.toggle("hidden", !allFinished);
  }

  function attachPhoneStreamListeners(sel) {
    const stream = dom.simNotifsStream;

    // Action button clicks
    stream.querySelectorAll(".act-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const card = e.target.closest(".sim-notif-card");
        const nid = card.getAttribute("data-nid");
        const notif = sel.active_week_notifications.find((n) => n.id === nid);
        if (!notif) return;

        notif.action = e.target.getAttribute("data-act");
        if (notif.action === "opened" && !notif.duration) {
          notif.duration = "few_seconds";
          notif.timing = "right_away";
        }
        renderTab1();
      });
    });

    // Duration clicks
    stream.querySelectorAll(".pill-opt[data-dur]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const card = e.target.closest(".sim-notif-card");
        const nid = card.getAttribute("data-nid");
        const notif = sel.active_week_notifications.find((n) => n.id === nid);
        if (!notif) return;
        notif.duration = e.target.getAttribute("data-dur");
        renderTab1();
      });
    });

    // Timing clicks
    stream.querySelectorAll(".pill-opt[data-time]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const card = e.target.closest(".sim-notif-card");
        const nid = card.getAttribute("data-nid");
        const notif = sel.active_week_notifications.find((n) => n.id === nid);
        if (!notif) return;
        notif.timing = e.target.getAttribute("data-time");
        renderTab1();
      });
    });

    // Toggles
    stream.querySelectorAll(".chk-tapped").forEach((chk) => {
      chk.addEventListener("change", (e) => {
        const card = e.target.closest(".sim-notif-card");
        const nid = card.getAttribute("data-nid");
        const notif = sel.active_week_notifications.find((n) => n.id === nid);
        if (notif) notif.clicked = e.target.checked;
      });
    });

    stream.querySelectorAll(".chk-saved").forEach((chk) => {
      chk.addEventListener("change", (e) => {
        const card = e.target.closest(".sim-notif-card");
        const nid = card.getAttribute("data-nid");
        const notif = sel.active_week_notifications.find((n) => n.id === nid);
        if (notif) notif.saved = e.target.checked;
      });
    });
  }

  function validateSubmitButton(sel) {
    if (sel.is_finished) {
      dom.submitWeekBtn.disabled = true;
      return;
    }
    const notifs = sel.active_week_notifications || [];
    const allActed = notifs.length === 6 && notifs.every((n) => !!n.action);
    dom.submitWeekBtn.disabled = !allActed;
    dom.submitHelpText.textContent = allActed
      ? "All 6 alerts reviewed. Click to submit week."
      : "Choose an action for all 6 alerts to submit";
  }

  // --- TAB 2: Customer Notifications ---
  function switchTab2Subview(subview) {
    appState.tab2Subview = subview;
    if (subview === "inboxes") {
      dom.segInboxesBtn.classList.add("active");
      dom.segInboxesBtn.setAttribute("aria-selected", "true");
      dom.segComposeBtn.classList.remove("active");
      dom.segComposeBtn.setAttribute("aria-selected", "false");
      dom.subviewInboxes.classList.remove("hidden");
      dom.subviewCompose.classList.add("hidden");
      renderTab2Inboxes();
    } else {
      dom.segComposeBtn.classList.add("active");
      dom.segComposeBtn.setAttribute("aria-selected", "true");
      dom.segInboxesBtn.classList.remove("active");
      dom.segInboxesBtn.setAttribute("aria-selected", "false");
      dom.subviewCompose.classList.remove("hidden");
      dom.subviewInboxes.classList.add("hidden");
      renderTab2Compose();
    }
  }

  function renderTab2() {
    renderTab2Inboxes();
    renderTab2Compose();
  }

  function renderTab2Inboxes() {
    const custs = appState.customers;
    const sel = appState.selectedCustomer;
    if (!sel) return;

    // Sidebar
    dom.notifCustList.innerHTML = custs
      .map((c) => {
        const isSel = c.id === sel.id;
        const status = c.status || "not_played";
        return `
          <div class="sidebar-cust-item ${isSel ? "selected" : ""}" data-cid="${c.id}">
            <div class="sidebar-cust-left">
              <span class="status-dot ${status}"></span>
              <div>
                <div class="sidebar-cust-name">${c.name}</div>
                <div class="sidebar-cust-status">${c.status_label}</div>
              </div>
            </div>
            <span class="phone-count-line">${c.frequency > 0 ? c.frequency + "/wk" : ""}</span>
          </div>
        `;
      })
      .join("");

    dom.notifCustList.querySelectorAll(".sidebar-cust-item").forEach((item) => {
      item.addEventListener("click", () => {
        selectCustomer(item.getAttribute("data-cid"));
      });
    });

    // Output Phone Content
    dom.outPhoneAvatar.textContent = sel.initials;
    dom.outPhoneName.textContent = sel.name;

    const analysis = sel.analysis;
    const isUnsub = sel.is_unsubscribed || (analysis && analysis.is_unsubscribed);

    // If Compare with Before is active
    if (appState.compareWithBefore) {
      dom.outStatusPill.className = "status-indicator-pill";
      dom.outStatusPill.textContent = "Standard Broadcast";
      dom.outPhoneCount.textContent = "12 notifications this week (Unfiltered flood)";

      dom.outNotifsStream.innerHTML = appState.standardBundle
        .map(
          (b) => `
          <div class="output-notif-card">
            <div class="output-notif-top">
              <span class="category-tag ${b.type}">
                ${CATEGORY_ICONS[b.type]}
                <span>${b.type_name}</span>
              </span>
              <span class="notif-time">${b.day}, ${b.time}</span>
            </div>
            <div class="sim-notif-text">${b.text}</div>
          </div>
        `
        )
        .join("");

      dom.continueCustomerBtn.disabled = true;
      return;
    }

    // Personalized Schedule Display
    dom.continueCustomerBtn.disabled = isUnsub || !analysis;

    if (isUnsub) {
      dom.outStatusPill.className = "status-indicator-pill unsubscribed";
      dom.outStatusPill.textContent = "Unsubscribed";
      dom.outPhoneCount.textContent = "No notifications";
      dom.outNotifsStream.innerHTML = `
        <div class="empty-phone-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
          </svg>
          <div class="empty-phone-title">No notifications</div>
          <p>Customer has unsubscribed from all communication.</p>
        </div>
      `;
    } else if (!analysis) {
      dom.outStatusPill.className = "status-indicator-pill not_played";
      dom.outStatusPill.textContent = "Not Played";
      dom.outPhoneCount.textContent = "Complete 5 simulation weeks to personalize";
      dom.outNotifsStream.innerHTML = `
        <div class="empty-phone-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <div class="empty-phone-title">No personalized schedule yet</div>
          <p>Simulate this customer's responses in Tab 1 and run the system.</p>
        </div>
      `;
    } else {
      const statusClass = analysis.status;
      dom.outStatusPill.className = `status-indicator-pill ${statusClass}`;
      dom.outStatusPill.textContent = analysis.status_label;
      dom.outPhoneCount.textContent = `${analysis.frequency} notifications this week`;

      const notifs = sel.continued_notifications || [];
      if (notifs.length === 0) {
        dom.outNotifsStream.innerHTML = `
          <div class="empty-phone-state">
            <div class="empty-phone-title">No notifications scheduled</div>
          </div>
        `;
      } else {
        dom.outNotifsStream.innerHTML = notifs
          .map(
            (n) => `
            <div class="output-notif-card ${n._slideIn ? "slide-in" : ""}">
              <div class="output-notif-top">
                <span class="category-tag ${n.type}">
                  ${CATEGORY_ICONS[n.type]}
                  <span>${n.type_name}</span>
                  ${n.is_recheck ? `<span class="recheck-badge">Re-check</span>` : ""}
                </span>
                <span class="notif-time">${n.day}, ${n.time}</span>
              </div>
              <div class="sim-notif-text">${n.text}</div>
            </div>
          `
          )
          .join("");
      }
    }
  }

  // --- TAB 2 SUBVIEW 2: Send a Notification ---
  const cachedRecentActivity = {};

  async function fetchRecentActivity(cid) {
    try {
      const res = await fetch(`/api/compose/activity?customer_id=${cid}`);
      const data = await res.json();
      if (data.ok) {
        cachedRecentActivity[cid] = data.items || [];
        renderRecentActivity(cid);
      }
    } catch (e) {
      console.error("Failed to fetch activity:", e);
    }
  }

  function renderRecentActivity(cid) {
    const items = cachedRecentActivity[cid] || [];
    if (!dom.recentActivityList) return;

    if (items.length === 0) {
      dom.recentActivityList.innerHTML = `<div class="recent-act-empty">No recent composed activity for this customer.</div>`;
      return;
    }

    dom.recentActivityList.innerHTML = items
      .map((item) => {
        let chipHtml = "";
        let actionLinkHtml = "";

        if (item.status === "sent") {
          chipHtml = `
            <span class="recent-act-chip sent">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Sent now</span>
            </span>
          `;
        } else if (item.status === "scheduled") {
          chipHtml = `
            <span class="recent-act-chip scheduled">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <span>${item.scheduled_time || "Scheduled"}</span>
            </span>
          `;
          actionLinkHtml = `<button type="button" class="recent-act-link btn-cancel-sched" data-item-id="${item.id}">Cancel</button>`;
        } else if (item.status === "cancelled") {
          chipHtml = `
            <span class="recent-act-chip not_sent">
              <span>Cancelled</span>
            </span>
          `;
        } else {
          chipHtml = `
            <span class="recent-act-chip not_sent">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
              <span>Not sent</span>
            </span>
          `;
          actionLinkHtml = `<button type="button" class="recent-act-link btn-override-send" data-item-id="${item.id}">Send anyway</button>`;
        }

        return `
          <div class="recent-act-item">
            <div class="recent-act-left">
              ${chipHtml}
              <span class="recent-act-text" title="${item.text}">${item.item || item.type_name}: ${item.highlight || item.text}</span>
            </div>
            ${actionLinkHtml}
          </div>
        `;
      })
      .join("");

    dom.recentActivityList.querySelectorAll(".btn-cancel-sched").forEach((btn) => {
      btn.addEventListener("click", () => handleCancelSchedule(btn.getAttribute("data-item-id")));
    });
    dom.recentActivityList.querySelectorAll(".btn-override-send").forEach((btn) => {
      btn.addEventListener("click", () => handleOverride(btn.getAttribute("data-item-id")));
    });
  }

  function renderTab2Compose() {
    if (!dom.composeActiveLayout) return;

    if (!appState.systemRun) {
      dom.composePrereqBanner.classList.remove("hidden");
      dom.composeActiveLayout.classList.add("hidden");
      return;
    }

    dom.composePrereqBanner.classList.add("hidden");
    dom.composeActiveLayout.classList.remove("hidden");

    // 1. Customer Select Options
    const custs = appState.customers;
    const currentCompId = appState.composeState.customerId || (appState.selectedCustomer ? appState.selectedCustomer.id : (custs[0] ? custs[0].id : "aarav"));
    appState.composeState.customerId = currentCompId;

    dom.composeCustomerSelect.innerHTML = custs
      .map((c) => {
        const isSel = c.id === currentCompId;
        const unsubText = c.is_unsubscribed ? " (Unsubscribed)" : "";
        const role = c.role_hint ? ` — ${c.role_hint}` : "";
        const style = c.is_unsubscribed ? "style='color:var(--text-muted);'" : "";
        return `<option value="${c.id}" ${isSel ? "selected" : ""} ${style}>${c.name}${role}${unsubText}</option>`;
      })
      .join("");

    const compCust = custs.find((c) => c.id === currentCompId) || appState.selectedCustomer;
    if (dom.composeCustHintText && compCust) {
      if (compCust.is_unsubscribed) {
        dom.composeCustHintText.textContent = `${compCust.name} has unsubscribed. All alerts will be rejected.`;
      } else if (compCust.analysis && compCust.analysis.risk_level === "High") {
        dom.composeCustHintText.textContent = `${compCust.name} is close to leaving (${compCust.role_hint}). Only Order Updates can be sent.`;
      } else if (compCust.id === "aarav") {
        dom.composeCustHintText.textContent = `Aarav loves offers & sales! Try generating an Offer in the morning.`;
      } else if (compCust.id === "kabir") {
        dom.composeCustHintText.textContent = `Kabir likes price drops, but ignores offers. Usually active in the morning.`;
      } else if (compCust.id === "diya") {
        dom.composeCustHintText.textContent = `Diya only cares about Order Updates. Promotional alerts will be blocked to prevent churn.`;
      } else if (compCust.id === "sanya") {
        dom.composeCustHintText.textContent = `Sanya is a fan of New Arrivals! Try generating a New Arrival alert.`;
      } else if (compCust.id === "vivaan") {
        dom.composeCustHintText.textContent = `Vivaan is highly engaged and opens most notifications.`;
      } else if (compCust.id === "anaya") {
        dom.composeCustHintText.textContent = `Anaya skims quickly and taps Price Drops.`;
      } else if (compCust.id === "meera") {
        dom.composeCustHintText.textContent = `Meera loves offers! Try generating an Offer alert.`;
      } else if (compCust.id === "ishita" || compCust.id === "rohan") {
        dom.composeCustHintText.textContent = `${compCust.name} is at risk of leaving (${compCust.role_hint}). Try sending an Order Update.`;
      } else {
        dom.composeCustHintText.textContent = `${compCust.name}: ${compCust.role_hint || "Test personalized delivery"}.`;
      }
    }

    // 2. Notification Type Chips
    dom.composeTypeChips.querySelectorAll(".chip-option-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-type") === appState.composeState.type);
    });

    // 3. Category Chips
    dom.composeCategoryChips.querySelectorAll(".chip-option-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-cat") === appState.composeState.category);
    });

    // 4. Items Select (dependent on category)
    const validItems = COMPOSE_CATEGORY_ITEMS[appState.composeState.category] || [];
    if (!validItems.includes(appState.composeState.item)) {
      appState.composeState.item = validItems[0] || "";
    }
    dom.composeItemSelect.innerHTML = validItems
      .map((item) => `<option value="${item}" ${item === appState.composeState.item ? "selected" : ""}>${item}</option>`)
      .join("");

    // 5. Highlights Select (dependent on type)
    const validHighlights = COMPOSE_TYPE_HIGHLIGHTS[appState.composeState.type] || [];
    if (!validHighlights.includes(appState.composeState.highlight)) {
      appState.composeState.highlight = validHighlights[0] || "";
    }
    dom.composeHighlightSelect.innerHTML = validHighlights
      .map((h) => `<option value="${h}" ${h === appState.composeState.highlight ? "selected" : ""}>${h}</option>`)
      .join("");

    // 6. Urgency (Fixed essential if Order Update)
    if (appState.composeState.type === "order_update") {
      dom.composeUrgencyChips.classList.add("hidden");
      dom.composeEssentialNote.classList.remove("hidden");
      appState.composeState.urgency = "essential";
    } else {
      dom.composeUrgencyChips.classList.remove("hidden");
      dom.composeEssentialNote.classList.add("hidden");
      if (appState.composeState.urgency === "essential") {
        appState.composeState.urgency = "normal";
      }
      dom.composeUrgencyChips.querySelectorAll(".chip-option-btn").forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-urgency") === appState.composeState.urgency);
      });
    }

    // Button disabled state
    dom.composeGenerateBtn.disabled = appState.composeState.isSubmitting || !appState.composeState.item || !appState.composeState.highlight;

    // Right Column Preview
    const compCust = custs.find((c) => c.id === currentCompId) || appState.selectedCustomer;
    if (compCust) {
      dom.compPhoneAvatar.textContent = compCust.initials;
      dom.compPhoneName.textContent = compCust.name;
      dom.recActCustName.textContent = compCust.name;

      const isUnsub = compCust.is_unsubscribed || (compCust.analysis && compCust.analysis.is_unsubscribed);
      const notifs = compCust.continued_notifications || [];

      if (isUnsub) {
        dom.compStatusPill.className = "status-indicator-pill unsubscribed";
        dom.compStatusPill.textContent = "Unsubscribed";
        dom.compPhoneCount.textContent = "No notifications";
        dom.compNotifsStream.innerHTML = `
          <div class="empty-phone-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
            </svg>
            <div class="empty-phone-title">No notifications</div>
            <p>Customer has unsubscribed from all communication.</p>
          </div>
        `;
      } else {
        const statusClass = compCust.analysis ? compCust.analysis.status : (compCust.status || "not_played");
        dom.compStatusPill.className = `status-indicator-pill ${statusClass}`;
        dom.compStatusPill.textContent = compCust.status_label || (compCust.analysis ? compCust.analysis.status_label : "Not played");
        dom.compPhoneCount.textContent = `${notifs.length} notifications this week`;

        if (notifs.length === 0) {
          dom.compNotifsStream.innerHTML = `
            <div class="empty-phone-state">
              <div class="empty-phone-title">No notifications scheduled</div>
              <p>Generate a notification on the left to test delivery.</p>
            </div>
          `;
        } else {
          dom.compNotifsStream.innerHTML = notifs
            .map(
              (n) => `
              <div class="output-notif-card ${n._slideIn ? "slide-in" : ""}">
                <div class="output-notif-top">
                  <span class="category-tag ${n.type}">
                    ${CATEGORY_ICONS[n.type]}
                    <span>${n.type_name}</span>
                    ${n.is_recheck ? `<span class="recheck-badge">Re-check</span>` : ""}
                  </span>
                  <span class="notif-time">${n.day}, ${n.time}</span>
                </div>
                <div class="sim-notif-text">${n.text}</div>
              </div>
            `
            )
            .join("");
        }
      }

      fetchRecentActivity(currentCompId);
    }

    // Demo Time Buttons active state
    dom.demoTimeSelector.querySelectorAll(".demo-time-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-time") === appState.demoTime);
    });
  }

  // --- Modals & Toasts ---
  function showToast(message, type = "success") {
    if (!dom.toastContainer) return;
    const toast = document.createElement("div");
    toast.className = `toast-item toast-${type}`;
    const icon = type === "success"
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;color:var(--status-green);flex-shrink:0;"><polyline points="20 6 9 17 4 12"/></svg>`
      : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;color:var(--accent-primary);flex-shrink:0;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    toast.innerHTML = `${icon}<span>${message}</span>`;
    dom.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function openModal(modalEl) {
    if (appState.activeModal) {
      appState.activeModal.classList.add("hidden");
    }
    modalEl.classList.remove("hidden");
    appState.activeModal = modalEl;
    const focusable = modalEl.querySelector("button, [tabindex='0']");
    if (focusable) focusable.focus();
  }

  function closeModal(modalEl) {
    modalEl.classList.add("hidden");
    if (appState.activeModal === modalEl) {
      appState.activeModal = null;
    }
  }

  let pendingOverrideItemId = null;

  async function handleGenerateNotification() {
    if (appState.composeState.isSubmitting) return;
    appState.composeState.isSubmitting = true;
    renderTab2Compose();

    try {
      const payload = {
        customer_id: appState.composeState.customerId,
        type: appState.composeState.type,
        category: appState.composeState.category,
        item: appState.composeState.item,
        highlight: appState.composeState.highlight,
        urgency: appState.composeState.urgency,
        demo_time: appState.demoTime
      };

      const res = await fetch("/api/compose/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok || !data.ok) {
        let msg = data.detail || "Could not generate notification";
        if (msg === "Not Found" || res.status === 404) {
          msg = "Please ensure the system is running and refresh the page.";
        }
        showToast(msg, "info");
        return;
      }

      appState.composeState.lastEvaluatedItem = data.item;
      await fetchState();

      if (data.item.decision === "send_now") {
        const compCust = appState.customers.find((c) => c.id === appState.composeState.customerId);
        if (compCust && compCust.continued_notifications && compCust.continued_notifications.length > 0) {
          compCust.continued_notifications[0]._slideIn = true;
        }
        renderTab2();
        showToast(`Sent to ${data.item.customer_name}`, "success");
      } else if (data.item.decision === "schedule") {
        dom.modalSchedCust.textContent = `Customer: ${data.item.customer_name}`;
        dom.modalSchedTime.textContent = data.item.scheduled_time || "Scheduled";
        dom.modalSchedReason.textContent = data.item.reason;
        dom.modalSchedPreview.textContent = data.item.text;
        openModal(dom.modalScheduled);
      } else {
        dom.modalNotSentCust.textContent = `Customer: ${data.item.customer_name}`;
        dom.modalNotSentReason.textContent = data.item.reason;
        dom.modalNotSentPreview.textContent = data.item.text;
        openModal(dom.modalNotSent);
      }

      fetchRecentActivity(appState.composeState.customerId);
    } catch (err) {
      console.error("Failed to generate notification:", err);
      showToast("Failed to generate notification", "info");
    } finally {
      appState.composeState.isSubmitting = false;
      renderTab2Compose();
    }
  }

  function handleOverride(itemId) {
    pendingOverrideItemId = itemId;
    openModal(dom.modalConfirmOverride);
  }

  async function executeOverride(itemId) {
    try {
      const res = await fetch("/api/compose/override", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: itemId })
      });
      const data = await res.json();
      if (data.ok) {
        closeModal(dom.modalConfirmOverride);
        if (dom.modalScheduled) closeModal(dom.modalScheduled);
        if (dom.modalNotSent) closeModal(dom.modalNotSent);

        await fetchState();
        const compCust = appState.customers.find((c) => c.id === data.item.customer_id);
        if (compCust && compCust.continued_notifications && compCust.continued_notifications.length > 0) {
          compCust.continued_notifications[0]._slideIn = true;
        }
        renderTab2();
        showToast(`Sent to ${data.item.customer_name}`, "success");
        fetchRecentActivity(data.item.customer_id);
      }
    } catch (e) {
      console.error("Override failed:", e);
    }
  }

  async function handleCancelSchedule(itemId) {
    try {
      const res = await fetch("/api/compose/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: itemId })
      });
      const data = await res.json();
      if (data.ok) {
        closeModal(dom.modalScheduled);
        fetchRecentActivity(appState.composeState.customerId);
        showToast("Schedule cancelled", "info");
      }
    } catch (e) {
      console.error("Cancel failed:", e);
    }
  }

  async function handleAdvanceDemoTime(timeSlot) {
    try {
      appState.demoTime = timeSlot;
      dom.demoTimeSelector.querySelectorAll(".demo-time-btn").forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-time") === timeSlot);
      });

      const res = await fetch("/api/compose/advance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ demo_time: timeSlot })
      });
      const data = await res.json();
      if (data.ok) {
        await fetchState();
        if (data.delivered_items && data.delivered_items.length > 0) {
          data.delivered_items.forEach((item) => {
            showToast(`Scheduled notification delivered to ${item.customer_name}`, "success");
          });
          const compCust = appState.customers.find((c) => c.id === appState.composeState.customerId);
          if (compCust && compCust.continued_notifications && compCust.continued_notifications.length > 0) {
            compCust.continued_notifications[0]._slideIn = true;
          }
        }
        renderTab2();
        fetchRecentActivity(appState.composeState.customerId);
      }
    } catch (e) {
      console.error("Advance failed:", e);
    }
  }

  // --- TAB 3: Customer Insights ---
  function renderTab3() {
    const metrics = appState.summaryMetrics;
    dom.metricEngaged.textContent = metrics.engaged || 0;
    dom.metricLosing.textContent = metrics.losing_interest || 0;
    dom.metricRisk.textContent = metrics.at_risk || 0;
    dom.metricUnsub.textContent = metrics.unsubscribed || 0;
    dom.metricAvoided.textContent = metrics.total_avoided || 0;

    const custs = appState.customers;
    const sel = appState.selectedCustomer;
    if (!sel) return;

    // Sidebar
    dom.insightsCustList.innerHTML = custs
      .map((c) => {
        const isSel = c.id === sel.id;
        const status = c.status || "not_played";
        return `
          <div class="sidebar-cust-item ${isSel ? "selected" : ""}" data-cid="${c.id}">
            <div class="sidebar-cust-left">
              <span class="status-dot ${status}"></span>
              <div>
                <div class="sidebar-cust-name">${c.name}</div>
                <div class="sidebar-cust-status">${c.status_label}</div>
              </div>
            </div>
          </div>
        `;
      })
      .join("");

    dom.insightsCustList.querySelectorAll(".sidebar-cust-item").forEach((item) => {
      item.addEventListener("click", () => {
        selectCustomer(item.getAttribute("data-cid"));
      });
    });

    const analysis = sel.analysis;
    dom.insAvatar.textContent = sel.initials;
    dom.insName.textContent = sel.name;

    if (!analysis) {
      dom.insTopInterest.textContent = "Run system in Tab 1 to generate insights";
      dom.insStatusBadge.className = "ins-status-badge not_played";
      dom.insStatusBadge.textContent = "Not Played";
      dom.insInterestsList.innerHTML = `<p style="color:var(--text-muted);font-size:0.85rem;">No data yet.</p>`;
      dom.insChartContainer.innerHTML = `<p style="color:var(--text-muted);font-size:0.85rem;">No activity.</p>`;
      dom.insLikelyBehavior.textContent = "Awaiting customer simulation.";
      dom.insObservationsList.innerHTML = `<li>Complete all 5 weeks to run the system.</li>`;
      dom.insFrequencyLine.textContent = "—";
      dom.insDecisionsContainer.innerHTML = "";
      dom.insRecActionTitle.textContent = "Simulation required";
      dom.insRecActionDesc.textContent = "Simulate 5 weeks of customer interaction first.";
      return;
    }

    // Status Badge
    dom.insStatusBadge.className = `ins-status-badge ${analysis.status}`;
    dom.insStatusBadge.textContent = analysis.status_label;
    dom.insTopInterest.textContent = `Top interest: ${analysis.top_interest}`;

    // 1. Interests Bars
    const interests = analysis.interests;
    dom.insInterestsList.innerHTML = Object.keys(interests)
      .map((k) => {
        const item = interests[k];
        const lvlClass = item.level.toLowerCase();
        return `
          <div class="interest-item">
            <div class="interest-meta">
              <span>${item.display_name}</span>
              <span>${item.level}</span>
            </div>
            <div class="interest-bar-track">
              <div class="interest-bar-fill ${lvlClass}"></div>
            </div>
          </div>
        `;
      })
      .join("");

    // 2. Engagement Over Time (Clean Inline SVG Sparkline)
    const trendClass = analysis.trend.toLowerCase();
    dom.insTrendBadge.className = `trend-badge ${trendClass}`;
    dom.insTrendBadge.textContent = analysis.trend;

    const weeksData = analysis.week_engagements || [0, 0, 0, 0, 0];
    dom.insChartContainer.innerHTML = renderSparklineSvg(weeksData);

    // 3. Likely Behaviour & Risk
    const riskClass = analysis.risk_level.toLowerCase();
    dom.insRiskBadge.className = `risk-badge ${riskClass}`;
    dom.insRiskBadge.textContent = `Risk: ${analysis.risk_level}`;
    dom.insLikelyBehavior.textContent = analysis.likely_behavior;

    // 4. Key Observations
    dom.insObservationsList.innerHTML = (analysis.observations || [])
      .map((obs) => `<li>${obs}</li>`)
      .join("");

    // 5. Decisions
    dom.insFrequencyLine.innerHTML = `<strong>${analysis.frequency} notifications per week</strong>`;
    let decisionsHtml = "";

    (analysis.continued_types || []).forEach((c) => {
      decisionsHtml += `
        <div class="decision-row">
          <span class="decision-badge continued">Continued</span>
          <div class="decision-desc">
            <strong>${c.name}</strong>
            <span>${c.reason}</span>
          </div>
        </div>
      `;
    });

    (analysis.paused_types || []).forEach((p) => {
      decisionsHtml += `
        <div class="decision-row">
          <span class="decision-badge paused">Paused</span>
          <div class="decision-desc">
            <strong>${p.name}</strong>
            <span>${p.reason}</span>
          </div>
        </div>
      `;
    });

    dom.insDecisionsContainer.innerHTML = decisionsHtml;

    // 6. Recommended Action
    dom.insRecActionTitle.textContent = analysis.recommended_action;
    if (analysis.recommended_action === "No action needed") {
      dom.insRecActionDesc.textContent = "Customer is naturally engaged. Maintain the personalized notification schedule.";
    } else if (analysis.recommended_action === "Reduce frequency") {
      dom.insRecActionDesc.textContent = "Engagement is cooling down. Focus only on top interest categories at a lower cadence.";
    } else if (analysis.recommended_action === "Send a re-engagement message") {
      dom.insRecActionDesc.textContent = "Customer is at immediate risk of leaving. Pause promotional noise and send an essential re-engagement offer.";
    } else {
      dom.insRecActionDesc.textContent = "Customer has opted out of all notifications.";
    }
  }

  function renderSparklineSvg(data) {
    const width = 340;
    const height = 120;
    const padding = 20;

    const points = data.map((val, idx) => {
      const x = padding + (idx * (width - 2 * padding)) / (data.length - 1);
      const y = height - padding - val * (height - 2 * padding);
      return { x, y, val };
    });

    const pathD = points
      .map((pt, i) => `${i === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`)
      .join(" ");

    const circles = points
      .map(
        (pt, i) => `
        <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="4.5" fill="var(--accent-primary)"/>
        <text x="${pt.x.toFixed(1)}" y="${height - 4}" text-anchor="middle" font-size="10" font-weight="600" fill="var(--text-muted)">W${i + 1}</text>
      `
      )
      .join("");

    return `
      <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;">
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="var(--border-light)" stroke-width="1.5" stroke-dasharray="3 3"/>
        <line x1="${padding}" y1="${padding}" x2="${width - padding}" y2="${padding}" stroke="var(--border-light)" stroke-width="1.5" stroke-dasharray="3 3"/>
        <path d="${pathD}" fill="none" stroke="var(--accent-primary)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        ${circles}
      </svg>
    `;
  }

  // =========================================================================
  // CONTINUED ROUND (TAB 2)
  // =========================================================================

  function openContinuedDrawer() {
    const sel = appState.selectedCustomer;
    if (!sel || !sel.continued_notifications) return;

    dom.contCustName.textContent = sel.name;
    dom.continuedDrawer.classList.remove("hidden");

    dom.contNotifsStream.innerHTML = sel.continued_notifications
      .map(
        (n) => `
        <div class="sim-notif-card" data-cid="${n.id}">
          <div class="sim-notif-top">
            <span class="category-tag ${n.type}">
              ${CATEGORY_ICONS[n.type]}
              <span>${n.type_name}</span>
              ${n.is_recheck ? `<span class="recheck-badge">Re-check alert</span>` : ""}
            </span>
            <span class="notif-time">${n.day}, ${n.time}</span>
          </div>
          <div class="sim-notif-text">${n.text}</div>
          
          <div class="action-buttons-group">
            <button type="button" class="act-btn" data-act="opened">Open</button>
            <button type="button" class="act-btn" data-act="ignored">Ignore</button>
            <button type="button" class="act-btn" data-act="dismissed">Dismiss</button>
            <button type="button" class="act-btn danger" data-act="muted">Mute</button>
            <button type="button" class="act-btn danger" data-act="unsubscribed">Unsubscribe</button>
          </div>
        </div>
      `
      )
      .join("");

    attachDrawerListeners();
  }

  function attachDrawerListeners() {
    const stream = dom.contNotifsStream;
    stream.querySelectorAll(".act-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const card = e.target.closest(".sim-notif-card");
        card.querySelectorAll(".act-btn").forEach((b) => b.classList.remove("active"));
        e.target.classList.add("active");

        const allChecked = Array.from(stream.querySelectorAll(".sim-notif-card")).every((c) =>
          c.querySelector(".act-btn.active")
        );
        dom.contSubmitBtn.disabled = !allChecked;
      });
    });
  }

  async function submitContinuedDrawer() {
    const sel = appState.selectedCustomer;
    if (!sel) return;

    const cards = dom.contNotifsStream.querySelectorAll(".sim-notif-card");
    const actions = [];
    cards.forEach((c) => {
      const id = c.getAttribute("data-cid");
      const activeBtn = c.querySelector(".act-btn.active");
      const act = activeBtn ? activeBtn.getAttribute("data-act") : "ignored";
      actions.push({ id, action: act });
    });

    try {
      await fetch(`/api/customer/${sel.id}/continue-act`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ actions })
      });
      dom.continuedDrawer.classList.add("hidden");
      await fetchState();
    } catch (err) {
      console.error("Failed to submit continued actions:", err);
    }
  }

  // =========================================================================
  // 60-SECOND AUTO DEMO MODE
  // =========================================================================

  async function startAutoDemo() {
    appState.autoDemoRunning = true;
    appState.autoDemoPaused = false;
    appState.autoDemoStep = 0;

    dom.demoController.classList.remove("hidden");
    dom.demoPauseBtn.textContent = "Pause";

    runAutoDemoFlow();
  }

  function stopAutoDemo() {
    appState.autoDemoRunning = false;
    appState.autoDemoPaused = false;
    clearTimeout(appState.autoDemoTimer);
    dom.demoController.classList.add("hidden");
    dom.demoProgressFill.style.width = "0%";
  }

  function togglePauseAutoDemo() {
    if (!appState.autoDemoRunning) return;
    appState.autoDemoPaused = !appState.autoDemoPaused;
    dom.demoPauseBtn.textContent = appState.autoDemoPaused ? "Resume" : "Pause";
    if (!appState.autoDemoPaused) {
      runAutoDemoFlow();
    }
  }

  async function waitAutoDemo(ms) {
    return new Promise((resolve) => {
      const start = Date.now();
      const check = () => {
        if (!appState.autoDemoRunning) return;
        if (appState.autoDemoPaused) {
          appState.autoDemoTimer = setTimeout(check, 200);
          return;
        }
        if (Date.now() - start >= ms) {
          resolve();
        } else {
          appState.autoDemoTimer = setTimeout(check, 100);
        }
      };
      check();
    });
  }

  async function runAutoDemoFlow() {
    const steps = [
      {
        text: "Step 1: Navigating to Tab 1 (Simulate Customers)...",
        pct: 10,
        action: async () => {
          switchTab("tab-simulate");
          appState.roleHintsVisible = true;
          dom.roleHintsToggle.checked = true;
          renderTab1();
          await waitAutoDemo(4000);
        }
      },
      {
        text: "Step 2: Loading sample behavior for all scripted personas...",
        pct: 25,
        action: async () => {
          await loadSampleBehaviour();
          await waitAutoDemo(4000);
        }
      },
      {
        text: "Step 3: Running ShopEasy intelligence engine...",
        pct: 45,
        action: async () => {
          await runSystem();
          await waitAutoDemo(4000);
        }
      },
      {
        text: "Step 4: Comparing Aarav (Offers) vs Diya (Order Updates Only)...",
        pct: 60,
        action: async () => {
          switchTab("tab-notifications");
          await selectCustomer("aarav");
          await waitAutoDemo(4000);
          await selectCustomer("diya");
          await waitAutoDemo(4000);
          await selectCustomer("arjun");
          await waitAutoDemo(4000);
        }
      },
      {
        text: "Step 5: Comparing against before (Generic 12-alert flood)...",
        pct: 75,
        action: async () => {
          dom.compareToggle.checked = true;
          appState.compareWithBefore = true;
          renderTab2();
          await waitAutoDemo(5000);
          dom.compareToggle.checked = false;
          appState.compareWithBefore = false;
          renderTab2();
          await waitAutoDemo(3000);
        }
      },
      {
        text: "Step 6: Inspecting Customer Insights in Tab 3...",
        pct: 90,
        action: async () => {
          switchTab("tab-insights");
          await selectCustomer("rohan");
          await waitAutoDemo(5000);
          await selectCustomer("meera");
          await waitAutoDemo(5000);
          await selectCustomer("ishita");
          await waitAutoDemo(4000);
        }
      },
      {
        text: "Auto Demo Complete! Feel free to explore freely.",
        pct: 100,
        action: async () => {
          await waitAutoDemo(3000);
          stopAutoDemo();
        }
      }
    ];

    while (appState.autoDemoStep < steps.length && appState.autoDemoRunning) {
      const curStep = steps[appState.autoDemoStep];
      dom.demoStatusText.textContent = curStep.text;
      dom.demoProgressFill.style.width = `${curStep.pct}%`;
      await curStep.action();
      appState.autoDemoStep++;
    }
  }

  // =========================================================================
  // EVENT LISTENERS
  // =========================================================================

  function setupEventListeners() {
    // Tab switching
    dom.tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        switchTab(btn.getAttribute("data-tab"));
      });
    });

    // Theme toggle
    dom.themeToggleBtn.addEventListener("click", toggleTheme);

    // Keyboard navigation
    window.addEventListener("keydown", handleKeyboardNav);

    // Reset Modal
    dom.resetBtn.addEventListener("click", () => {
      dom.resetModal.classList.remove("hidden");
    });
    dom.resetCancelBtn.addEventListener("click", () => {
      dom.resetModal.classList.add("hidden");
    });
    dom.resetConfirmBtn.addEventListener("click", resetDemo);

    // Auto Demo Controls
    dom.autoDemoBtn.addEventListener("click", startAutoDemo);
    dom.demoStopBtn.addEventListener("click", stopAutoDemo);
    dom.demoPauseBtn.addEventListener("click", togglePauseAutoDemo);

    // Role hints toggle
    dom.roleHintsToggle.addEventListener("change", (e) => {
      appState.roleHintsVisible = e.target.checked;
      renderTab1();
    });

    // Play selected customer button
    dom.playCustomerBtn.addEventListener("click", () => {
      if (appState.selectedCustomer) {
        autoPlayCustomer(appState.selectedCustomer.id);
      }
    });

    // Load sample behaviour
    dom.loadSampleBtn.addEventListener("click", loadSampleBehaviour);

    // Submit week button in phone
    dom.submitWeekBtn.addEventListener("click", () => {
      if (!appState.selectedCustomer) return;
      const actions = (appState.selectedCustomer.active_week_notifications || []).map((n) => ({
        id: n.id,
        action: n.action,
        duration: n.duration,
        timing: n.timing,
        clicked: n.clicked,
        saved: n.saved
      }));
      submitWeekActions(appState.selectedCustomer.id, actions);
    });

    // Run system button
    dom.runSystemBtn.addEventListener("click", runSystem);

    // Compare with before toggle
    dom.compareToggle.addEventListener("change", (e) => {
      appState.compareWithBefore = e.target.checked;
      renderTab2();
    });

    // Continue as this customer button
    dom.continueCustomerBtn.addEventListener("click", openContinuedDrawer);
    dom.contCancelBtn.addEventListener("click", () => {
      dom.continuedDrawer.classList.add("hidden");
    });
    dom.contSubmitBtn.addEventListener("click", submitContinuedDrawer);

    // Tab 2 Segmented Control
    if (dom.segInboxesBtn && dom.segComposeBtn) {
      dom.segInboxesBtn.addEventListener("click", () => switchTab2Subview("inboxes"));
      dom.segComposeBtn.addEventListener("click", () => switchTab2Subview("compose"));
    }

    // Compose Prereq Button
    if (dom.composeGoSimBtn) {
      dom.composeGoSimBtn.addEventListener("click", () => switchTab("tab-simulate"));
    }

    // Compose Customer Select
    if (dom.composeCustomerSelect) {
      dom.composeCustomerSelect.addEventListener("change", async (e) => {
        appState.composeState.customerId = e.target.value;
        await selectCustomer(e.target.value);
        renderTab2Compose();
      });
    }

    // Compose Notification Type Chips
    if (dom.composeTypeChips) {
      dom.composeTypeChips.querySelectorAll(".chip-option-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          appState.composeState.type = btn.getAttribute("data-type");
          renderTab2Compose();
        });
      });
    }

    // Compose Category Chips
    if (dom.composeCategoryChips) {
      dom.composeCategoryChips.querySelectorAll(".chip-option-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          appState.composeState.category = btn.getAttribute("data-cat");
          renderTab2Compose();
        });
      });
    }

    // Compose Item Select
    if (dom.composeItemSelect) {
      dom.composeItemSelect.addEventListener("change", (e) => {
        appState.composeState.item = e.target.value;
        dom.composeGenerateBtn.disabled = appState.composeState.isSubmitting || !appState.composeState.item || !appState.composeState.highlight;
      });
    }

    // Compose Highlight Select
    if (dom.composeHighlightSelect) {
      dom.composeHighlightSelect.addEventListener("change", (e) => {
        appState.composeState.highlight = e.target.value;
        dom.composeGenerateBtn.disabled = appState.composeState.isSubmitting || !appState.composeState.item || !appState.composeState.highlight;
      });
    }

    // Compose Urgency Chips
    if (dom.composeUrgencyChips) {
      dom.composeUrgencyChips.querySelectorAll(".chip-option-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          appState.composeState.urgency = btn.getAttribute("data-urgency");
          renderTab2Compose();
        });
      });
    }

    // Generate Notification Button
    if (dom.composeGenerateBtn) {
      dom.composeGenerateBtn.addEventListener("click", handleGenerateNotification);
    }

    // Demo Time Buttons
    if (dom.demoTimeSelector) {
      dom.demoTimeSelector.querySelectorAll(".demo-time-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          handleAdvanceDemoTime(btn.getAttribute("data-time"));
        });
      });
    }

    // Scheduled Modal buttons
    if (dom.modalSchedOkBtn) {
      dom.modalSchedOkBtn.addEventListener("click", () => closeModal(dom.modalScheduled));
    }
    if (dom.modalSchedCancelBtn) {
      dom.modalSchedCancelBtn.addEventListener("click", () => {
        if (appState.composeState.lastEvaluatedItem) {
          handleCancelSchedule(appState.composeState.lastEvaluatedItem.id);
        }
      });
    }
    if (dom.modalSchedOverrideBtn) {
      dom.modalSchedOverrideBtn.addEventListener("click", () => {
        if (appState.composeState.lastEvaluatedItem) {
          handleOverride(appState.composeState.lastEvaluatedItem.id);
        }
      });
    }

    // Not Sent Modal buttons
    if (dom.modalNotSentOkBtn) {
      dom.modalNotSentOkBtn.addEventListener("click", () => closeModal(dom.modalNotSent));
    }
    if (dom.modalNotSentOverrideBtn) {
      dom.modalNotSentOverrideBtn.addEventListener("click", () => {
        if (appState.composeState.lastEvaluatedItem) {
          handleOverride(appState.composeState.lastEvaluatedItem.id);
        }
      });
    }

    // Confirm Override Modal buttons
    if (dom.modalConfirmCancelBtn) {
      dom.modalConfirmCancelBtn.addEventListener("click", () => closeModal(dom.modalConfirmOverride));
    }
    if (dom.modalConfirmProceedBtn) {
      dom.modalConfirmProceedBtn.addEventListener("click", () => {
        if (pendingOverrideItemId) {
          executeOverride(pendingOverrideItemId);
        }
      });
    }

    // Modal Backdrop clicks to close
    [dom.modalScheduled, dom.modalNotSent, dom.modalConfirmOverride].forEach((m) => {
      if (m) {
        m.addEventListener("click", (e) => {
          if (e.target === m) closeModal(m);
        });
      }
    });
  }

  // Kickoff on load
  document.addEventListener("DOMContentLoaded", init);
})();
