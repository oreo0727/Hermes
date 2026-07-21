const state = {
  snapshot: null,
  runs: [],
  dispatches: [],
  alerts: [],
  truthLoop: null,
  truthLoopRunning: false,
  realityLayer: null,
  realityCaptureRunning: false,
  repairBay: null,
  repairRunning: false,
  brainGraph: null,
  selectedBrainNodeId: "",
  brainGroupFilter: "all",
  brainHitTargets: [],
  chatMessages: [],
  chatSessionId: "",
  loading: false,
  chatLoading: false,
  voiceListening: false,
  voiceRecognition: null,
  voiceSupported: false,
};

const elements = {
  refreshButton: document.querySelector("#refresh-button"),
  navLinks: Array.from(document.querySelectorAll(".nav-link")),
  topbarEyebrow: document.querySelector("#topbar-eyebrow"),
  topbarTitle: document.querySelector("#topbar-title"),
  dashboardPage: document.querySelector("#dashboard-page"),
  brainPage: document.querySelector("#brain-page"),
  portalLabel: document.querySelector("#portal-label"),
  sidebarQuote: document.querySelector("#sidebar-quote"),
  heroQuote: document.querySelector("#hero-quote"),
  heroQuoteAttribution: document.querySelector("#hero-quote-attribution"),
  footerDiscord: document.querySelector("#footer-discord"),
  footerSystem: document.querySelector("#footer-system"),
  operatorPresence: document.querySelector("#operator-presence"),
  operatorSubtitle: document.querySelector("#operator-subtitle"),
  operatorActiveSlice: document.querySelector("#operator-active-slice"),
  operatorProof: document.querySelector("#operator-proof"),
  metricProjects: document.querySelector("#metric-projects"),
  metricTasks: document.querySelector("#metric-tasks"),
  metricBlocked: document.querySelector("#metric-blocked"),
  metricCompleted: document.querySelector("#metric-completed"),
  blockedPill: document.querySelector("#blocked-pill"),
  blockedDetails: document.querySelector("#blocked-details"),
  blockedClose: document.querySelector("#blocked-close"),
  blockedList: document.querySelector("#blocked-list"),
  activeProjects: document.querySelector("#active-projects"),
  chatForm: document.querySelector("#chat-form"),
  chatInput: document.querySelector("#chat-input"),
  chatLog: document.querySelector("#chat-log"),
  chatSend: document.querySelector("#chat-send"),
  chatStatus: document.querySelector("#chat-status"),
  floatingChatWidget: document.querySelector("#sheldon-chat-widget"),
  floatingChatToggle: document.querySelector("#sheldon-chat-toggle"),
  floatingChatPopover: document.querySelector("#sheldon-chat-popover"),
  floatingChatClose: document.querySelector("#sheldon-chat-close"),
  floatingChatForm: document.querySelector("#floating-chat-form"),
  floatingChatInput: document.querySelector("#floating-chat-input"),
  floatingChatLog: document.querySelector("#floating-chat-log"),
  floatingChatSend: document.querySelector("#floating-chat-send"),
  floatingChatStatus: document.querySelector("#floating-chat-status"),
  voiceToggles: Array.from(document.querySelectorAll("[data-voice-toggle]")),
  queueTable: document.querySelector("#queue-table"),
  agentTeam: document.querySelector("#agent-team"),
  agentTheater: document.querySelector("#agent-theater"),
  agentRadar: document.querySelector("#agent-radar"),
  truthLoopRun: document.querySelector("#truth-loop-run"),
  truthLoopView: document.querySelector("#truth-loop-view"),
  realityForm: document.querySelector("#reality-form"),
  realityNote: document.querySelector("#reality-note"),
  realityMode: document.querySelector("#reality-mode"),
  realityFile: document.querySelector("#reality-file"),
  realitySubmit: document.querySelector("#reality-submit"),
  realityStatus: document.querySelector("#reality-status"),
  realityView: document.querySelector("#reality-view"),
  repairCount: document.querySelector("#repair-count"),
  repairView: document.querySelector("#repair-view"),
  activityFeed: document.querySelector("#activity-feed"),
  brainStats: document.querySelector("#brain-stats"),
  brainLegend: document.querySelector("#brain-legend"),
  brainGroupFilters: document.querySelector("#brain-group-filters"),
  brainTableList: document.querySelector("#brain-table-list"),
  brainDatabaseBadge: document.querySelector("#brain-database-badge"),
  brainNodeCount: document.querySelector("#brain-node-count"),
  brainEdgeCount: document.querySelector("#brain-edge-count"),
  brainGraphCanvas: document.querySelector("#brain-graph-canvas"),
  brainInspector: document.querySelector("#brain-inspector"),
  brainSearch: document.querySelector("#brain-search"),
  brainRefresh: document.querySelector("#brain-refresh"),
  emptyStateTemplate: document.querySelector("#empty-state-template"),
};

const laneIconMap = {
  "creative-dev": "palette",
  "app-dev": "atom",
  "game-dev": "gamepad",
  operator: "flask",
};

function cloneEmptyState() {
  return elements.emptyStateTemplate.content.firstElementChild.cloneNode(true);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

function text(value, fallback = "n/a") {
  const result = String(value || "").trim();
  return result || fallback;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function nl2br(value) {
  return escapeHtml(value).replaceAll("\n", "<br />");
}

function currentRoute() {
  return window.location.hash === "#brain" ? "brain" : "dashboard";
}

function setActiveNav() {
  const hash = window.location.hash || "#dashboard";
  const activeHash = hash === "#brain" ? "#brain" : hash;
  for (const link of elements.navLinks || []) {
    link.classList.toggle("active", link.getAttribute("href") === activeHash);
  }
}

function applyRoute() {
  const route = currentRoute();
  const isBrain = route === "brain";
  if (elements.dashboardPage) {
    elements.dashboardPage.hidden = isBrain;
  }
  if (elements.brainPage) {
    elements.brainPage.hidden = !isBrain;
  }
  if (elements.topbarEyebrow) {
    elements.topbarEyebrow.textContent = isBrain ? "Database Lens" : "Management UI";
  }
  if (elements.topbarTitle) {
    elements.topbarTitle.textContent = isBrain ? "Brain DB" : "Command Deck";
  }
  setActiveNav();
  if (isBrain) {
    window.requestAnimationFrame(renderBrainGraph);
    return;
  }
  const anchor = window.location.hash ? document.querySelector(window.location.hash) : null;
  if (anchor && anchor !== elements.dashboardPage) {
    window.requestAnimationFrame(() => anchor.scrollIntoView({ block: "start" }));
  }
}

function relativeTime(value) {
  if (!value) {
    return "n/a";
  }
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) {
    return String(value);
  }
  const diffMs = target.getTime() - Date.now();
  const diffMinutes = Math.round(diffMs / 60000);
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  if (Math.abs(diffMinutes) < 60) {
    return rtf.format(diffMinutes, "minute");
  }
  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 48) {
    return rtf.format(diffHours, "hour");
  }
  return rtf.format(Math.round(diffHours / 24), "day");
}

function setChatStatus(label, tone = "ready") {
  if (elements.chatStatus) {
    elements.chatStatus.textContent = label;
    elements.chatStatus.dataset.tone = tone;
  }
  if (elements.floatingChatStatus) {
    elements.floatingChatStatus.textContent = label;
    elements.floatingChatStatus.dataset.tone = tone;
  }
}

function setVoiceButtonState(listening) {
  state.voiceListening = Boolean(listening);
  if (!elements.voiceToggles.length) {
    return;
  }
  for (const button of elements.voiceToggles) {
    button.setAttribute("aria-pressed", listening ? "true" : "false");
    button.textContent = listening ? "Listening..." : "Voice";
  }
}

function speakSheldonReply(content) {
  if (!("speechSynthesis" in window)) {
    return;
  }
  const clean = String(content || "").trim();
  if (!clean) {
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.02;
  utterance.pitch = 0.96;
  utterance.volume = 1;
  window.speechSynthesis.speak(utterance);
}

function initVoiceMode() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  state.voiceSupported = Boolean(Recognition && "speechSynthesis" in window);
  if (!elements.voiceToggles.length) {
    return;
  }
  if (!state.voiceSupported) {
    for (const button of elements.voiceToggles) {
      button.disabled = true;
      button.textContent = "No Voice";
      button.title = "This browser does not expose speech recognition and speech synthesis.";
    }
    return;
  }
  const recognition = new Recognition();
  recognition.lang = "en-US";
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;
  recognition.onstart = () => {
    openFloatingChat();
    setVoiceButtonState(true);
    setChatStatus("Listening", "busy");
  };
  recognition.onerror = (event) => {
    setVoiceButtonState(false);
    setChatStatus(`Voice error: ${event.error || "unknown"}`, "error");
  };
  recognition.onend = () => {
    setVoiceButtonState(false);
    if (!state.chatLoading) {
      setChatStatus("Ready", "ready");
    }
  };
  recognition.onresult = (event) => {
    let transcript = "";
    let finalTranscript = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const result = event.results[index];
      const textResult = result[0]?.transcript || "";
      transcript += textResult;
      if (result.isFinal) {
        finalTranscript += textResult;
      }
    }
    if (elements.floatingChatInput && transcript.trim()) {
      elements.floatingChatInput.value = transcript.trim();
    }
    const outgoing = finalTranscript.trim();
    if (outgoing) {
      sendChatMessage(outgoing, { speak: true });
    }
  };
  state.voiceRecognition = recognition;
}

function toggleVoiceMode() {
  if (!state.voiceRecognition) {
    setChatStatus("Voice unavailable", "error");
    return;
  }
  if (state.voiceListening) {
    state.voiceRecognition.stop();
    return;
  }
  try {
    window.speechSynthesis?.cancel();
    state.voiceRecognition.start();
  } catch (error) {
    setVoiceButtonState(false);
    setChatStatus(String(error.message || error), "error");
  }
}

function chatMessageElement(role, content) {
  const isUser = role === "user";
  const article = document.createElement("article");
  article.className = `chat-message ${isUser ? "user" : "assistant"}`;
  article.innerHTML = `
    <div class="chat-avatar" aria-hidden="true">
      ${
        isUser
          ? '<span aria-hidden="true">You</span>'
          : '<img src="/branding/sheldon.png" alt="" draggable="false" />'
      }
    </div>
    <div class="chat-bubble">
      <strong>${isUser ? "You" : "Sheldon"}</strong>
      <p>${nl2br(content)}</p>
    </div>
  `;
  return article;
}

function appendChatMessage(role, content) {
  const message = {
    role,
    content: String(content || "").trim(),
  };
  if (!message.content) {
    return;
  }
  state.chatMessages.push(message);
  for (const log of [elements.chatLog, elements.floatingChatLog]) {
    if (!log) {
      continue;
    }
    log.append(chatMessageElement(role, message.content));
    log.scrollTop = log.scrollHeight;
  }
}

function setChatLoading(loading) {
  state.chatLoading = loading;
  for (const input of [elements.chatInput, elements.floatingChatInput]) {
    if (input) {
      input.disabled = loading;
    }
  }
  for (const sendButton of [elements.chatSend, elements.floatingChatSend]) {
    if (sendButton) {
      sendButton.disabled = loading;
      sendButton.textContent = loading ? "Thinking..." : "Send";
    }
  }
}

function openFloatingChat() {
  if (!elements.floatingChatWidget || !elements.floatingChatPopover) {
    return;
  }
  elements.floatingChatWidget.classList.add("open");
  elements.floatingChatPopover.hidden = false;
  elements.floatingChatToggle?.setAttribute("aria-label", "Close Sheldon chat");
  setTimeout(() => elements.floatingChatInput?.focus(), 80);
}

function closeFloatingChat() {
  if (!elements.floatingChatWidget || !elements.floatingChatPopover) {
    return;
  }
  elements.floatingChatWidget.classList.remove("open");
  elements.floatingChatPopover.hidden = true;
  elements.floatingChatToggle?.setAttribute("aria-label", "Open Sheldon chat");
}

function toggleFloatingChat() {
  if (elements.floatingChatWidget?.classList.contains("open")) {
    closeFloatingChat();
  } else {
    openFloatingChat();
  }
}

async function sendChatMessage(content, options = {}) {
  const outgoing = String(content || "").trim();
  if (!outgoing || state.chatLoading) {
    return "";
  }

  appendChatMessage("user", outgoing);
  for (const input of [elements.chatInput, elements.floatingChatInput]) {
    if (input) {
      input.value = "";
    }
  }
  setChatLoading(true);
  setChatStatus("Sheldon is thinking", "busy");

  try {
    const active = activeProject();
    const payload = {
      profile: "operator",
      fast: true,
      project_id: active?.project_id || "",
      session_id: state.chatSessionId,
      messages: state.chatMessages.slice(-12),
    };
    const response = await fetchJson("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.fast_path && response.session_id) {
      state.chatSessionId = response.session_id;
    }
    const reply = response.content || "I received the message, but no response text came back.";
    appendChatMessage("assistant", reply);
    if (options.speak) {
      speakSheldonReply(reply);
    }
    setChatStatus(response.fast_path ? "Fast route" : (response.session_id ? "Session linked" : "Ready"), "ready");
    return reply;
  } catch (error) {
    const message = String(error.message || error);
    const reply = `I could not reach the operator gateway cleanly: ${message}`;
    appendChatMessage("assistant", reply);
    if (options.speak) {
      speakSheldonReply(reply);
    }
    setChatStatus("Gateway error", "error");
    return reply;
  } finally {
    setChatLoading(false);
    if (elements.floatingChatWidget?.classList.contains("open")) {
      elements.floatingChatInput?.focus();
    } else {
      elements.chatInput?.focus();
    }
  }
}

function statusTone(status) {
  const normalized = String(status || "").toLowerCase();
  if (["completed", "connected", "active", "healthy", "running", "ready", "live", "online"].includes(normalized)) {
    return "good";
  }
  if (["queued", "attention", "blocked", "elevated", "warm", "in progress"].includes(normalized)) {
    return "warn";
  }
  if (["failed", "archived", "interrupted", "disconnected", "error", "high", "offline"].includes(normalized)) {
    return "bad";
  }
  return "neutral";
}

function activeProject() {
  const snapshot = state.snapshot;
  if (!snapshot) {
    return null;
  }
  const activeProjectId = String((snapshot.portfolio || {}).active_project_id || "");
  return (
    (snapshot.projects || []).find((project) => String(project.project_id || "") === activeProjectId) ||
    (snapshot.projects || [])[0] ||
    null
  );
}

function agentByProfile(profileKey) {
  return (state.snapshot?.agents || []).find((agent) => agent.profile_key === profileKey) || null;
}

function activeRunCount() {
  return state.runs.filter((run) => ["queued", "running"].includes(String(run.status || ""))).length;
}

function activeDispatchCount() {
  return state.dispatches.filter((dispatch) => ["queued", "running"].includes(String(dispatch.status || ""))).length;
}

function projectSessionBinding(project) {
  return (project?.portfolio?.session_bindings || []).find((binding) => binding.platform === "discord") || null;
}

function priorityLabel(project) {
  const score = Number(project.priority_score || 0);
  if (score >= 70) {
    return "high";
  }
  if (score >= 45) {
    return "medium";
  }
  return "low";
}

function laneBadge(agent, lane) {
  const title = text(agent?.title, lane);
  const name = text(agent?.character_name, lane);
  return `${title} (${name})`;
}

function iconMarkup(name) {
  if (name === "palette") {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20h1.2a2.8 2.8 0 0 0 0-5.6H11A2 2 0 0 1 9 14.4 9.4 9.4 0 0 1 18.4 5H19a3 3 0 0 0 0-3Zm-5 8.2a1.2 1.2 0 1 1 1.2-1.2A1.2 1.2 0 0 1 7 10.2Zm3-4.2a1.2 1.2 0 1 1 1.2-1.2A1.2 1.2 0 0 1 10 6Zm4 0a1.2 1.2 0 1 1 1.2-1.2A1.2 1.2 0 0 1 14 6Zm3 4.2a1.2 1.2 0 1 1 1.2-1.2A1.2 1.2 0 0 1 17 10.2Z"/></svg>';
  }
  if (name === "atom") {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3c-1.67 0-3.22 2.29-4.11 5.75C4.35 9.64 2 11.19 2 12.86s2.35 3.22 5.89 4.11C8.78 20.71 10.33 23 12 23s3.22-2.29 4.11-5.75C19.65 15.36 22 13.81 22 12.14s-2.35-3.22-5.89-4.11C15.22 5.29 13.67 3 12 3Zm0 2c.56 0 1.47 1.04 2.14 3.1A20.27 20.27 0 0 0 9.86 8.1C10.53 6.04 11.44 5 12 5Zm-4.79 5.02A18.37 18.37 0 0 1 12 9.39a18.37 18.37 0 0 1 4.79.63A18.37 18.37 0 0 1 17.42 12a18.37 18.37 0 0 1-.63 1.98A18.37 18.37 0 0 1 12 14.61a18.37 18.37 0 0 1-4.79-.63A18.37 18.37 0 0 1 6.58 12a18.37 18.37 0 0 1 .63-1.98ZM4 12.86c0-.56 1.04-1.47 3.1-2.14A20.27 20.27 0 0 0 7.1 15c-2.06-.67-3.1-1.58-3.1-2.14Zm16 0c0 .56-1.04 1.47-3.1 2.14a20.27 20.27 0 0 0 0-4.28c2.06.67 3.1 1.58 3.1 2.14ZM12 21c-.56 0-1.47-1.04-2.14-3.1a20.27 20.27 0 0 0 4.28 0C13.47 19.96 12.56 21 12 21Zm0-7a2 2 0 1 0-2-2 2 2 0 0 0 2 2Z"/></svg>';
  }
  if (name === "gamepad") {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 8h10a4 4 0 0 1 3.91 4.85l-.7 3.13A3 3 0 0 1 15.3 17.6l-2.14-1.43a2 2 0 0 0-2.22 0L8.8 17.6a3 3 0 0 1-4.91-1.62l-.7-3.13A4 4 0 0 1 7 8Zm-.5 2.5v1.5H5v2h1.5V15h2v-1.5H10v-2H8.5v-1.5Zm10 1a1 1 0 1 0 1 1 1 1 0 0 0-1-1Zm-2 2a1 1 0 1 0 1 1 1 1 0 0 0-1-1Z"/></svg>';
  }
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6l1 4h3v3h-2l-2 11H9L7 10H5V7h3Zm2 7v8h2v-8Z"/></svg>';
}

function renderHeader() {
  const snapshot = state.snapshot || {};
  elements.portalLabel.textContent = text(snapshot.portal?.label, "Hermes v2 Command Deck");
}

function renderHero() {
  const snapshot = state.snapshot || {};
  const active = activeProject();
  const blockedProjects = (snapshot.projects || []).filter((project) => Number(project.blocked_count || 0) > 0).length;
  const closedProjects = (snapshot.projects || []).filter((project) => ["completed", "archived"].includes(String(project.status || "").toLowerCase())).length;
  const operator = agentByProfile("operator");
  const discordConnected = (operator?.connected_platforms || []).includes("discord");

  elements.metricProjects.textContent = String((snapshot.projects || []).length);
  elements.metricTasks.textContent = String(activeRunCount() + activeDispatchCount());
  elements.metricBlocked.textContent = String(blockedProjects);
  elements.metricCompleted.textContent = String(closedProjects);

  elements.operatorPresence.textContent = active
    ? "Good evening, Operator."
    : "Hermes is standing by.";
  elements.operatorSubtitle.textContent = active
    ? `${text(active.title)} is progressing within ${text(active.loop_risk, "acceptable")} loop risk.`
    : "No focused project is active yet.";
  elements.operatorActiveSlice.textContent = active ? text(active.focused_slice, active.title) : "No focused slice";
  elements.operatorProof.textContent = active
    ? `${Number(active.proof_count || 0)} proof item${Number(active.proof_count || 0) === 1 ? "" : "s"} linked`
    : "No proof attached";

  elements.sidebarQuote.textContent = discordConnected
    ? '"Discord is primary. Truth is mandatory."'
    : '"Reconnect the operator surface before claiming flow."';
  elements.heroQuote.textContent = active && Number(active.blocked_count || 0) > 0
    ? "When something is blocked, the right move is to say so plainly."
    : "When something goes wrong, the optimal move is the truthful one.";
  elements.heroQuoteAttribution.textContent = "Sheldon, Operator";
  elements.footerDiscord.textContent = discordConnected ? "Discord Connected" : "Discord Disconnected";

  const liveAgents = (snapshot.agents || []).filter((agent) => agent.live).length;
  elements.footerSystem.textContent = liveAgents === (snapshot.agents || []).length
    ? "All systems operational"
    : `${liveAgents}/${(snapshot.agents || []).length} lanes live`;

  renderBlockedDetails();
}

function blockedItems() {
  const rows = [];
  for (const project of state.snapshot?.projects || []) {
    const blocked = Array.isArray(project.blocked) ? project.blocked : [];
    for (const item of blocked) {
      const detail = String(item || "").trim();
      if (!detail) {
        continue;
      }
      rows.push({ project, detail });
    }
  }
  return rows;
}

function blockedRowMarkup(row) {
  const project = row.project || {};
  return `
    <article class="blocked-row">
      <div>
        <strong>${escapeHtml(text(project.title, project.project_id))}</strong>
        <p>${escapeHtml(row.detail)}</p>
        <span>${escapeHtml(text(project.next, "No next step recorded."))}</span>
      </div>
      <button class="row-action" type="button" data-action="focus" data-project-id="${escapeHtml(project.project_id)}">Focus</button>
    </article>
  `;
}

function renderBlockedDetails() {
  if (!elements.blockedList) {
    return;
  }
  const rows = blockedItems();
  if (!rows.length) {
    elements.blockedList.innerHTML = `
      <article class="empty-state">
        <strong>No blockers recorded.</strong>
        <p class="meta">Hermes does not currently have a blocked item in project state.</p>
      </article>
    `;
    return;
  }
  elements.blockedList.innerHTML = rows.map(blockedRowMarkup).join("");
}

function setBlockedDetailsOpen(open) {
  if (!elements.blockedDetails || !elements.blockedPill) {
    return;
  }
  elements.blockedDetails.hidden = !open;
  elements.blockedPill.setAttribute("aria-expanded", open ? "true" : "false");
  if (open) {
    renderBlockedDetails();
    elements.blockedDetails.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

function progressBarMarkup(percent) {
  const clamped = Math.max(0, Math.min(100, Number(percent || 0)));
  return `
    <div class="progress">
      <span style="width:${clamped}%"></span>
    </div>
    <strong class="progress-value">${clamped}%</strong>
  `;
}

function projectRowMarkup(project) {
  const ownerAgent = agentByProfile(project.slice?.owner_lane || project.owner);
  const lane = project.slice?.owner_lane || project.owner;
  const iconName = laneIconMap[lane] || "flask";
  const binding = projectSessionBinding(project);
  const archived = String(project.status || "") === "archived";
  return `
    <article class="project-row" data-project-id="${escapeHtml(project.project_id)}">
      <div class="project-main">
        <div class="project-type-icon">${iconMarkup(iconName)}</div>
        <div class="project-copy">
          <div class="project-title-row">
            <h4>${escapeHtml(project.title)}</h4>
            <span class="lane-badge">${escapeHtml(laneBadge(ownerAgent, lane))}</span>
          </div>
          <p>${escapeHtml(text(project.summary))}</p>
        </div>
      </div>
      <div class="project-now">
        <span class="meta-label">Now</span>
        <p>${escapeHtml(text(project.now))}</p>
      </div>
      <div class="project-next">
        <span class="meta-label">Next</span>
        <p>${escapeHtml(text(project.next))}</p>
      </div>
      <div class="project-progress">
        ${progressBarMarkup(project.progress_percent)}
      </div>
      <div class="project-side">
        <div class="project-owner-avatar">
          ${
            ownerAgent?.avatar_path
              ? `<img src="${escapeHtml(ownerAgent.avatar_path)}" alt="${escapeHtml(text(ownerAgent.character_name))}" />`
              : `<span>${escapeHtml(text(ownerAgent?.character_name, "?").slice(0, 1))}</span>`
          }
        </div>
        <div class="project-actions">
          ${archived ? "" : `<button class="row-action" type="button" data-action="focus" data-project-id="${escapeHtml(project.project_id)}">Focus</button>`}
          ${archived ? "" : `<button class="row-action quiet" type="button" data-action="archive" data-project-id="${escapeHtml(project.project_id)}">Archive</button>`}
        </div>
        <p class="row-meta">${binding ? `Bound • ${escapeHtml(relativeTime(binding.updated_at))}` : `Proof • ${escapeHtml(String(project.proof_count || 0))}`}</p>
      </div>
    </article>
  `;
}

function renderProjects() {
  const projects = [...(state.snapshot?.projects || [])];
  elements.activeProjects.innerHTML = "";
  if (!projects.length) {
    elements.activeProjects.append(cloneEmptyState());
    return;
  }
  projects.sort((left, right) => {
    const leftActive = left.portfolio?.active ? 0 : 1;
    const rightActive = right.portfolio?.active ? 0 : 1;
    if (leftActive !== rightActive) {
      return leftActive - rightActive;
    }
    return Number(left.queue_rank || 9999) - Number(right.queue_rank || 9999);
  });
  elements.activeProjects.innerHTML = projects.slice(0, 4).map(projectRowMarkup).join("");
}

function queueRowMarkup(project) {
  const ownerAgent = agentByProfile(project.slice?.owner_lane || project.owner);
  const priority = priorityLabel(project);
  const status = project.portfolio?.active ? "In Progress" : (project.portfolio?.state === "queued" ? "Queued" : text(project.status));
  const eta = Number(project.progress_percent || 0) >= 80 ? "Soon" : Number(project.progress_percent || 0) >= 50 ? "Mid" : "Later";
  return `
    <div class="queue-row" data-project-id="${escapeHtml(project.project_id)}">
      <div class="queue-priority ${escapeHtml(priority)}">${escapeHtml(priority.toUpperCase())}</div>
      <div class="queue-task">
        <strong>${escapeHtml(text(project.focused_slice, project.title))}</strong>
        <p>${escapeHtml(project.title)}</p>
      </div>
      <div class="queue-agent">
        <div class="tiny-avatar">
          ${
            ownerAgent?.avatar_path
              ? `<img src="${escapeHtml(ownerAgent.avatar_path)}" alt="${escapeHtml(text(ownerAgent.character_name))}" />`
              : `<span>${escapeHtml(text(ownerAgent?.character_name, "?").slice(0, 1))}</span>`
          }
        </div>
        <span>${escapeHtml(text(ownerAgent?.character_name, project.owner))}</span>
      </div>
      <div class="queue-status tone-${statusTone(status)}">${escapeHtml(status)}</div>
      <div class="queue-eta">${escapeHtml(eta)}</div>
    </div>
  `;
}

function renderQueue() {
  const projects = [...(state.snapshot?.projects || [])];
  elements.queueTable.innerHTML = "";
  if (!projects.length) {
    elements.queueTable.append(cloneEmptyState());
    return;
  }
  projects.sort((left, right) => Number(right.priority_score || 0) - Number(left.priority_score || 0));
  elements.queueTable.innerHTML = `
    <div class="queue-head-row">
      <span>Priority</span>
      <span>Task</span>
      <span>Agent</span>
      <span>Status</span>
      <span>ETA</span>
    </div>
    ${projects.map(queueRowMarkup).join("")}
  `;
}

function teamRowMarkup(agent) {
  const live = Boolean(agent.live);
  const statusLabel = live ? "ONLINE" : text(agent.status, "OFFLINE").toUpperCase();
  return `
    <article class="team-row" style="--agent-accent:${escapeHtml(agent.accent)}">
      <div class="team-avatar">
        ${
          agent.avatar_path
            ? `<img src="${escapeHtml(agent.avatar_path)}" alt="${escapeHtml(agent.character_name)}" />`
            : `<span>${escapeHtml(agent.character_name.slice(0, 1))}</span>`
        }
        <span class="presence-dot ${live ? "live" : "offline"}"></span>
      </div>
      <div class="team-copy">
        <h4>${escapeHtml(agent.character_name)}</h4>
        <p class="team-role">${escapeHtml(agent.title)}</p>
        <p class="team-line">${escapeHtml(text(agent.role_summary))}</p>
      </div>
      <span class="team-status ${live ? "live" : "offline"}">${escapeHtml(statusLabel)}</span>
    </article>
  `;
}

function renderAgents() {
  const preferredOrder = ["operator", "creative-dev", "app-dev", "game-dev"];
  const agents = [...(state.snapshot?.agents || [])].sort(
    (left, right) => preferredOrder.indexOf(left.profile_key) - preferredOrder.indexOf(right.profile_key)
  );
  elements.agentTeam.innerHTML = "";
  if (!agents.length) {
    elements.agentTeam.append(cloneEmptyState());
    return;
  }
  elements.agentTeam.innerHTML = agents.map(teamRowMarkup).join("");
}

function theaterRowMarkup(row) {
  const confidence = Math.round(Number(row.confidence || 0) * 100);
  return `
    <article class="theater-row" style="--agent-accent:${escapeHtml(row.accent || "#84a5ff")}">
      <div class="theater-head">
        <div class="tiny-avatar">
          ${
            row.avatar_path
              ? `<img src="${escapeHtml(row.avatar_path)}" alt="${escapeHtml(row.character_name)}" />`
              : `<span>${escapeHtml(text(row.character_name, "?").slice(0, 1))}</span>`
          }
        </div>
        <div>
          <strong>${escapeHtml(text(row.character_name))}</strong>
          <span>${escapeHtml(text(row.next_move, "observe_and_update"))}</span>
        </div>
        <b>${escapeHtml(String(confidence))}%</b>
      </div>
      <p><span>Thought</span>${escapeHtml(text(row.current_thought))}</p>
      <p><span>Learning</span>${escapeHtml(text(row.learning))}</p>
      <p><span>Proof Gate</span>${escapeHtml(text(row.proof_gate))}</p>
    </article>
  `;
}

function renderTheater() {
  const rows = state.snapshot?.live_theater || [];
  elements.agentTheater.innerHTML = "";
  if (!rows.length) {
    elements.agentTheater.append(cloneEmptyState());
    return;
  }
  elements.agentTheater.innerHTML = rows.map(theaterRowMarkup).join("");
}

function latestByAgent(rows = []) {
  const result = new Map();
  for (const row of rows) {
    const slug = String(row.agent_slug || "");
    if (!slug || result.has(slug)) {
      continue;
    }
    result.set(slug, row);
  }
  return result;
}

function radarRowMarkup(agent) {
  const heartbeats = latestByAgent(state.snapshot?.always_on?.heartbeats || []);
  const intentions = latestByAgent(state.snapshot?.always_on?.intentions || []);
  const heartbeat = heartbeats.get(agent.slug) || {};
  const intention = intentions.get(agent.slug) || {};
  const status = text(intention.status || heartbeat.status, "waiting");
  const decision = text(intention.autonomy_decision, "listening");
  const workResult = intention.payload?.work_result || {};
  return `
    <article class="radar-row" style="--agent-accent:${escapeHtml(agent.accent || "#84a5ff")}">
      <div class="radar-pulse"></div>
      <div class="radar-copy">
        <strong>${escapeHtml(agent.character_name)} <span>${escapeHtml(status)}</span></strong>
        <p>${escapeHtml(text(workResult.summary || heartbeat.observation, agent.role_summary))}</p>
        <small>${escapeHtml(text(intention.title, heartbeat.intention || "No proposed action yet."))}</small>
      </div>
      <b>${escapeHtml(decision)}</b>
    </article>
  `;
}

function renderRadar() {
  const agents = state.snapshot?.agents || [];
  elements.agentRadar.innerHTML = "";
  if (!agents.length) {
    elements.agentRadar.append(cloneEmptyState());
    return;
  }
  elements.agentRadar.innerHTML = agents.map(radarRowMarkup).join("");
}

function truthLoopAgentMarkup(row) {
  const work = row.work_result || {};
  return `
    <article class="truth-agent-row">
      <strong>${escapeHtml(text(row.agent_slug, "agent"))}</strong>
      <span>${escapeHtml(text(row.status, "waiting"))}</span>
      <p>${escapeHtml(text(work.summary || row.title, "No movement recorded yet."))}</p>
    </article>
  `;
}

function renderTruthLoop() {
  if (!elements.truthLoopView) {
    return;
  }
  const payload = state.truthLoop || {};
  const latest = payload.latest || {};
  const movement = Array.isArray(latest.agent_movement) ? latest.agent_movement : [];
  const executions = Array.isArray(latest.executions) ? latest.executions : [];
  const score = payload.self_improvement?.average_score ?? latest.score_after ?? "n/a";
  if (!latest.receipt_id) {
    elements.truthLoopView.innerHTML = `
      <article class="truth-loop-empty">
        <strong>Truth Loop is armed.</strong>
        <p>Run it to refresh agent intentions, apply a safe self-improvement pass, and write a receipt into the brain.</p>
      </article>
    `;
    return;
  }
  elements.truthLoopView.innerHTML = `
    <article class="truth-loop-card">
      <div class="truth-loop-orb" aria-hidden="true"></div>
      <div class="truth-loop-copy">
        <strong>${escapeHtml(text(latest.summary, "Truth Loop ran."))}</strong>
        <p>Brain score: ${escapeHtml(String(score))} • Safe executions: ${escapeHtml(String(executions.length))} • ${escapeHtml(relativeTime(latest.updated_at || latest.created_at))}</p>
      </div>
    </article>
    <div class="truth-agent-list">
      ${movement.slice(0, 4).map(truthLoopAgentMarkup).join("") || "<p class=\"meta\">No agent movement in the latest receipt.</p>"}
    </div>
  `;
}

function activeProjectId() {
  const portfolioId = String(state.snapshot?.portfolio?.active_project_id || "").trim();
  if (portfolioId) {
    return portfolioId;
  }
  const active = (state.snapshot?.projects || []).find((project) => Boolean(project.portfolio?.active));
  return String(active?.project_id || "");
}

function setRealityStatus(label, tone = "ready") {
  if (!elements.realityStatus) {
    return;
  }
  elements.realityStatus.textContent = label;
  elements.realityStatus.dataset.tone = tone;
}

function realityCaptureMarkup(capture) {
  const route = capture.route || {};
  const attachments = Array.isArray(capture.attachments) ? capture.attachments : [];
  const handoff = capture.handoff || {};
  return `
    <article class="reality-capture-row">
      <div>
        <strong>${escapeHtml(text(capture.summary, "Field evidence captured."))}</strong>
        <p>${escapeHtml(text(capture.note, "No operator note supplied."))}</p>
        <span>${escapeHtml(text(capture.project_title, "Hermes portfolio"))} • ${escapeHtml(text(capture.mode, "field"))} • ${escapeHtml(relativeTime(capture.updated_at || capture.created_at))}</span>
      </div>
      <b>${escapeHtml(text(route.target, "sheldon"))}</b>
      ${
        attachments.length
          ? `<small>${escapeHtml(String(attachments.length))} image${attachments.length === 1 ? "" : "s"}${handoff.handoff_id ? " • handoff queued" : ""}</small>`
          : `<small>${handoff.handoff_id ? "handoff queued" : "receipt written"}</small>`
      }
    </article>
  `;
}

function renderRealityLayer() {
  if (!elements.realityView) {
    return;
  }
  const captures = state.realityLayer?.captures || [];
  if (!captures.length) {
    elements.realityView.innerHTML = `
      <article class="reality-empty">
        <strong>Sheldon Sight is ready.</strong>
        <p>Attach a screenshot/photo or write a field note. Hermes will route it to the right agent and write a receipt.</p>
      </article>
    `;
    return;
  }
  elements.realityView.innerHTML = captures.slice(0, 3).map(realityCaptureMarkup).join("");
}

function repairMarkup(repair) {
  const classification = repair.classification || {};
  const checks = Array.isArray(repair.diagnostics) ? repair.diagnostics : [];
  const passed = checks.filter((row) => row.ok).length;
  return `
    <article class="repair-row">
      <div class="repair-row-head">
        <div>
          <strong>${escapeHtml(text(repair.summary, "Repair lane ready."))}</strong>
          <p>${escapeHtml(text(repair.operator_note, "No operator note supplied."))}</p>
          <span>${escapeHtml(text(repair.project_title, "Hermes portfolio"))} • ${escapeHtml(text(classification.kind, "triage"))} • ${escapeHtml(text(repair.status, "triaged"))}</span>
        </div>
        <b>${escapeHtml(text(repair.owner, "sheldon"))}</b>
      </div>
      <div class="repair-checks">
        ${checks.slice(0, 3).map((check) => `<span class="${check.ok ? "ok" : "warn"}">${escapeHtml(check.name)}: ${escapeHtml(check.ok ? "ok" : "check")}</span>`).join("") || `<span class="warn">diagnostics pending</span>`}
      </div>
      <button class="row-action quiet" type="button" data-repair-run="${escapeHtml(repair.repair_id)}">${checks.length ? `Refresh diagnostics (${passed}/${checks.length})` : "Run diagnostics"}</button>
    </article>
  `;
}

function renderRepairBay() {
  if (!elements.repairView) {
    return;
  }
  const repairs = state.repairBay?.repairs || [];
  if (elements.repairCount) {
    elements.repairCount.textContent = `${state.repairBay?.open_count || 0} open`;
  }
  if (!repairs.length) {
    elements.repairView.innerHTML = `
      <article class="repair-empty">
        <strong>Repair Bay is standing by.</strong>
        <p>Every Sheldon Sight capture now opens a read-only repair lane with diagnostics, owner, proof, and guardrails.</p>
      </article>
    `;
    return;
  }
  elements.repairView.innerHTML = repairs.slice(0, 4).map(repairMarkup).join("");
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("Could not read file."));
    reader.readAsDataURL(file);
  });
}

function buildActivityFeed() {
  const activities = [];
  const latestTruth = state.truthLoop?.latest || {};
  if (latestTruth.receipt_id) {
    activities.push({
      type: "truth-loop",
      title: text(latestTruth.summary, "Truth Loop receipt"),
      detail: `${text(latestTruth.focus, "operator truth loop")} • ${text(latestTruth.status, "applied")}`,
      updated_at: latestTruth.updated_at || latestTruth.created_at,
      tone: "done",
      icon: "flask",
    });
  }
  const latestReality = state.realityLayer?.latest || {};
  if (latestReality.capture_id) {
    activities.push({
      type: "reality-layer",
      title: text(latestReality.summary, "Reality Layer capture"),
      detail: `${text(latestReality.project_title, "Hermes portfolio")} • ${text(latestReality.mode, "field")} • ${text(latestReality.route?.target, "sheldon")}`,
      updated_at: latestReality.updated_at || latestReality.created_at,
      tone: "working",
      icon: "atom",
    });
  }
  const latestRepair = state.repairBay?.latest || {};
  if (latestRepair.repair_id) {
    activities.push({
      type: "repair-bay",
      title: text(latestRepair.summary, "Repair Bay updated"),
      detail: `${text(latestRepair.project_title, "Hermes portfolio")} • ${text(latestRepair.owner, "sheldon")} • ${text(latestRepair.status, "triaged")}`,
      updated_at: latestRepair.updated_at || latestRepair.created_at,
      tone: "working",
      icon: "flask",
    });
  }
  for (const run of state.runs.slice(0, 6)) {
    const contractReady = run.contract_review ? Boolean(run.contract_review.ready) : true;
    const closureReady = run.closure_review ? Boolean(run.closure_review.ready) : false;
    const actionLabel = text(run.action_type, "direct_execute");
    activities.push({
      type: "run",
      title: text(run.latest_checkpoint || run.run_id, "Run updated"),
      detail: `${text(run.profile_key)} • ${text(run.project_id, "no project")} • ${actionLabel}${run.action_type === "close_slice" ? ` • ${closureReady ? "closure-ready" : "closure-held"}` : ""}${contractReady ? "" : " • contract-gap"}`,
      updated_at: run.updated_at || run.created_at,
      tone: contractReady ? statusTone(run.status) : "warn",
      icon: "flask",
    });
  }
  for (const dispatch of state.dispatches.slice(0, 6)) {
    const contractReady = dispatch.contract_review ? Boolean(dispatch.contract_review.ready) : true;
    activities.push({
      type: "dispatch",
      title: text(dispatch.output_preview || dispatch.dispatch_id, "Dispatch updated"),
      detail: `${text(dispatch.profile)} • ${text(dispatch.project_id, "no project")} • ${text(dispatch.action_type, "direct_execute")}${contractReady ? "" : " • contract-gap"}`,
      updated_at: dispatch.updated_at || dispatch.created_at,
      tone: contractReady ? statusTone(dispatch.status) : "warn",
      icon: laneIconMap[String(dispatch.profile || "").trim()] || "palette",
    });
  }
  for (const alert of state.alerts.slice(0, 6)) {
    activities.push({
      type: "alert",
      title: text(alert.title, "Alert"),
      detail: text(alert.summary, "Review needed"),
      updated_at: alert.updated_at,
      tone: statusTone(alert.kind),
      icon: "atom",
    });
  }
  activities.sort((left, right) => String(right.updated_at || "").localeCompare(String(left.updated_at || "")));
  return activities.slice(0, 8);
}

function activityRowMarkup(item) {
  return `
    <article class="activity-row tone-${escapeHtml(item.tone)}">
      <div class="activity-icon">${iconMarkup(item.icon)}</div>
      <div class="activity-copy">
        <strong>${escapeHtml(item.title)}</strong>
        <p>${escapeHtml(item.detail)}</p>
        <span>${escapeHtml(relativeTime(item.updated_at))}</span>
      </div>
      <div class="activity-check"></div>
    </article>
  `;
}

function renderActivity() {
  const activities = buildActivityFeed();
  elements.activityFeed.innerHTML = "";
  if (!activities.length) {
    elements.activityFeed.append(cloneEmptyState());
    return;
  }
  elements.activityFeed.innerHTML = activities.map(activityRowMarkup).join("");
}

const brainGroupMeta = {
  agent: { label: "Agents", color: "#f0a554" },
  memory: { label: "Memories", color: "#8fb4ff" },
  cognitive: { label: "Cognition", color: "#b694ff" },
  project: { label: "Projects", color: "#78cc59" },
  handoff: { label: "Handoffs", color: "#ff7782" },
  improvement: { label: "Improvement", color: "#4fd1c5" },
};

function brainNodeColor(group) {
  return brainGroupMeta[group]?.color || "#d8ddff";
}

function hexToRgba(hex, alpha) {
  const clean = String(hex || "").replace("#", "");
  if (clean.length !== 6) {
    return `rgba(168,139,250,${alpha})`;
  }
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function brainNodeRadius(node) {
  const weight = Math.max(0.3, Math.min(1.8, Number(node.weight || 1)));
  const base = node.group === "agent" ? 13 : node.group === "project" ? 10 : node.group === "memory" ? 7 : 6;
  return Math.round(base + weight * 2.1);
}

function filteredBrainGraph() {
  const graph = state.brainGraph || { nodes: [], edges: [] };
  const query = String(elements.brainSearch?.value || "").trim().toLowerCase();
  const groupFilter = state.brainGroupFilter || "all";
  const nodes = (graph.nodes || []).filter((node) => {
    if (groupFilter !== "all" && node.group !== groupFilter) {
      return false;
    }
    if (!query) {
      return true;
    }
    const haystack = [
      node.label,
      node.group,
      node.kind,
      node.detail,
      node.agent_slug,
      node.project_id,
      node.source,
    ].join(" ").toLowerCase();
    return haystack.includes(query);
  });
  const nodeIds = new Set(nodes.map((node) => node.id));
  return {
    ...graph,
    nodes,
    edges: (graph.edges || []).filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)),
  };
}

function seededAngle(id) {
  let hash = 0;
  for (const char of String(id)) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  }
  return (hash % 6283) / 1000;
}

function seededUnit(id, salt = "") {
  let hash = 2166136261;
  for (const char of `${id}:${salt}`) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4294967295;
}

function visibleBrainGraph(graph) {
  const degree = new Map();
  for (const edge of graph.edges || []) {
    degree.set(edge.source, (degree.get(edge.source) || 0) + Number(edge.weight || 1));
    degree.set(edge.target, (degree.get(edge.target) || 0) + Number(edge.weight || 1));
  }
  const selected = state.selectedBrainNodeId;
  const selectedNeighbors = new Set();
  if (selected) {
    selectedNeighbors.add(selected);
    for (const edge of graph.edges || []) {
      if (edge.source === selected) selectedNeighbors.add(edge.target);
      if (edge.target === selected) selectedNeighbors.add(edge.source);
    }
  }
  const searched = Boolean(String(elements.brainSearch?.value || "").trim());
  const limit = searched || state.brainGroupFilter !== "all" ? 118 : 72;
  const nodes = [...(graph.nodes || [])]
    .map((node) => ({
      ...node,
      visualScore:
        (degree.get(node.id) || 0) +
        Number(node.weight || 0) * 4 +
        (node.group === "agent" ? 120 : 0) +
        (node.group === "project" ? 62 : 0) +
        (node.group === "improvement" ? 34 : 0) +
        (selectedNeighbors.has(node.id) ? 95 : 0),
    }))
    .sort((left, right) => right.visualScore - left.visualScore)
    .slice(0, limit);
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = [...(graph.edges || [])]
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    .sort((left, right) => Number(right.weight || 0) - Number(left.weight || 0))
    .slice(0, 160);
  return { ...graph, nodes, edges, hiddenCount: Math.max(0, (graph.nodes || []).length - nodes.length) };
}

function positionedBrainNodes(nodes, edges, width, height) {
  const cx = width / 2;
  const cy = height / 2;
  const depth = 980;
  const perspective = 920;
  const groupPull = {
    agent: [0, 0, 220],
    project: [0, -height * 0.34, -140],
    memory: [-width * 0.24, 0, 60],
    cognitive: [width * 0.25, -height * 0.03, 40],
    handoff: [-width * 0.2, height * 0.33, -120],
    improvement: [width * 0.23, height * 0.32, 130],
  };
  const positioned = new Map();
  nodes.forEach((node, index) => {
    const angle = seededAngle(node.id);
    const radius = Math.min(width, height) * (0.16 + (index % 11) * 0.027);
    const z = (seededUnit(node.id, "z") - 0.5) * depth;
    positioned.set(node.id, {
      ...node,
      sx: Math.cos(angle) * radius,
      sy: Math.sin(angle) * radius,
      z,
      vx: 0,
      vy: 0,
      vz: 0,
    });
  });

  const graphEdges = (edges || []).filter((edge) => positioned.has(edge.source) && positioned.has(edge.target));
  for (let step = 0; step < 92; step += 1) {
    const rows = Array.from(positioned.values());
    for (let index = 0; index < rows.length; index += 1) {
      const left = rows[index];
      for (let j = index + 1; j < rows.length; j += 1) {
        const right = rows[j];
        const dx = right.sx - left.sx || 0.01;
        const dy = right.sy - left.sy || 0.01;
        const dz = right.z - left.z || 0.01;
        const distance = Math.max(38, Math.sqrt(dx * dx + dy * dy + dz * dz));
        const force = 1400 / (distance * distance);
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;
        const fz = (dz / distance) * force * 0.8;
        left.vx -= fx;
        left.vy -= fy;
        left.vz -= fz;
        right.vx += fx;
        right.vy += fy;
        right.vz += fz;
      }
    }
    for (const edge of graphEdges) {
      const source = positioned.get(edge.source);
      const target = positioned.get(edge.target);
      const dx = target.sx - source.sx;
      const dy = target.sy - source.sy;
      const dz = target.z - source.z;
      const distance = Math.max(1, Math.sqrt(dx * dx + dy * dy + dz * dz));
      const preferred = 150 + (1 - Math.min(1, Number(edge.weight || 0.6))) * 120;
      const force = (distance - preferred) * 0.0055;
      const fx = (dx / distance) * force;
      const fy = (dy / distance) * force;
      const fz = (dz / distance) * force * 0.8;
      source.vx += fx;
      source.vy += fy;
      source.vz += fz;
      target.vx -= fx;
      target.vy -= fy;
      target.vz -= fz;
    }
    for (const node of positioned.values()) {
      const [gx, gy, gz] = groupPull[node.group] || [0, 0, 0];
      node.vx += (gx - node.sx) * 0.0024;
      node.vy += (gy - node.sy) * 0.0024;
      node.vz += (gz - node.z) * 0.002;
      node.sx += node.vx;
      node.sy += node.vy;
      node.z += node.vz;
      node.vx *= 0.72;
      node.vy *= 0.72;
      node.vz *= 0.74;
      node.sx = Math.max(-width * 0.48, Math.min(width * 0.48, node.sx));
      node.sy = Math.max(-height * 0.48, Math.min(height * 0.48, node.sy));
      node.z = Math.max(-depth * 0.52, Math.min(depth * 0.52, node.z));
    }
  }
  for (const node of positioned.values()) {
    const scale = perspective / (perspective - node.z);
    node.depthScale = Math.max(0.54, Math.min(1.9, scale));
    node.x = Math.max(24, Math.min(width - 24, cx + node.sx * node.depthScale));
    node.y = Math.max(24, Math.min(height - 24, cy + node.sy * node.depthScale));
    node.depthOpacity = Math.max(0.22, Math.min(1, 0.58 + node.depthScale * 0.28));
  }
  return positioned;
}

function renderBrainStats(graph) {
  if (!elements.brainStats) {
    return;
  }
  const summary = graph?.summary || {};
  const database = graph?.database || {};
  const tables = database.tables || [];
  const tablePreview = tables.slice(0, 6).map((row) => `${row.name.replace("hermes_", "")}: ${row.rows}`).join(" • ");
  elements.brainStats.innerHTML = `
    <article class="brain-stat">
      <span class="meta-label">Backend</span>
      <strong>${escapeHtml(text(database.database, "unknown"))}</strong>
      <p>${escapeHtml(text(database.backend, "n/a"))}</p>
    </article>
    <article class="brain-stat">
      <span class="meta-label">Nodes</span>
      <strong>${escapeHtml(String(summary.nodes || 0))}</strong>
      <p>${escapeHtml(Object.entries(summary.groups || {}).map(([key, value]) => `${key}:${value}`).join(" • ") || "No nodes")}</p>
    </article>
    <article class="brain-stat">
      <span class="meta-label">Synapses</span>
      <strong>${escapeHtml(String(summary.edges || 0))}</strong>
      <p>${escapeHtml(Object.keys(summary.relations || {}).slice(0, 4).join(" • ") || "No edges")}</p>
    </article>
    <article class="brain-stat wide">
      <span class="meta-label">Tables</span>
      <strong>${escapeHtml(String(tables.length || 0))}</strong>
      <p>${escapeHtml(tablePreview || "File fallback graph")}</p>
    </article>
  `;
}

function renderBrainLegend(graph) {
  if (!elements.brainLegend) {
    return;
  }
  const groups = graph?.summary?.groups || {};
  elements.brainLegend.innerHTML = Object.entries(brainGroupMeta).map(([group, meta]) => `
    <span class="brain-legend-pill">
      <i style="background:${escapeHtml(meta.color)}"></i>
      ${escapeHtml(meta.label)}
      <b>${escapeHtml(String(groups[group] || 0))}</b>
    </span>
  `).join("");
}

function renderBrainVault(graph) {
  const summary = graph?.summary || {};
  const database = graph?.database || {};
  const groups = summary.groups || {};
  if (elements.brainDatabaseBadge) {
    elements.brainDatabaseBadge.textContent = text(database.database, "unknown");
  }
  if (elements.brainNodeCount) {
    elements.brainNodeCount.textContent = `${summary.nodes || 0} nodes`;
  }
  if (elements.brainEdgeCount) {
    elements.brainEdgeCount.textContent = `${summary.edges || 0} synapses`;
  }
  if (elements.brainGroupFilters) {
    const rows = [["all", "All", summary.nodes || 0], ...Object.entries(brainGroupMeta).map(([group, meta]) => [group, meta.label, groups[group] || 0])];
    elements.brainGroupFilters.innerHTML = rows.map(([group, label, count]) => `
      <button class="brain-group-filter ${state.brainGroupFilter === group ? "active" : ""}" type="button" data-brain-group="${escapeHtml(group)}">
        <i style="background:${escapeHtml(group === "all" ? "#d6d6d6" : brainNodeColor(group))}"></i>
        <span>${escapeHtml(label)}</span>
        <b>${escapeHtml(String(count))}</b>
      </button>
    `).join("");
  }
  if (elements.brainTableList) {
    const tables = database.tables || [];
    elements.brainTableList.innerHTML = tables.length
      ? tables.map((row) => `
          <button class="brain-table-row" type="button" data-table-query="${escapeHtml(row.name.replace("hermes_", ""))}">
            <span>${escapeHtml(row.name.replace("hermes_", ""))}</span>
            <b>${escapeHtml(String(row.rows))}</b>
          </button>
        `).join("")
      : `<p class="meta">File fallback graph. No table stats available.</p>`;
  }
}

function renderBrainInspector(nodeId = state.selectedBrainNodeId) {
  if (!elements.brainInspector) {
    return;
  }
  const graph = state.brainGraph || { nodes: [], edges: [] };
  const node = (graph.nodes || []).find((row) => row.id === nodeId);
  if (!node) {
    elements.brainInspector.innerHTML = `
      <p class="eyebrow">Inspector</p>
      <h4>Select a node</h4>
      <p class="meta">Click any memory, synapse endpoint, agent, project, or cognitive record to inspect its database source.</p>
    `;
    return;
  }
  const connected = (graph.edges || []).filter((edge) => edge.source === node.id || edge.target === node.id);
  const payloadPreview = JSON.stringify(node.payload || {}, null, 2);
  elements.brainInspector.innerHTML = `
    <p class="eyebrow">Inspector</p>
    <h4>${escapeHtml(node.label)}</h4>
    <div class="brain-inspector-badges">
      <span>${escapeHtml(node.group)}</span>
      <span>${escapeHtml(node.kind)}</span>
      ${node.agent_slug ? `<span>${escapeHtml(node.agent_slug)}</span>` : ""}
      ${node.project_id ? `<span>${escapeHtml(node.project_id)}</span>` : ""}
    </div>
    <p>${escapeHtml(text(node.detail, "No detail stored."))}</p>
    <dl class="brain-record-meta">
      <div><dt>Source</dt><dd>${escapeHtml(text(node.source, "unknown"))}</dd></div>
      <div><dt>Weight</dt><dd>${escapeHtml(String(Number(node.weight || 0).toFixed(2)))}</dd></div>
      <div><dt>Connections</dt><dd>${escapeHtml(String(connected.length))}</dd></div>
    </dl>
    <div class="brain-connections">
      ${connected.slice(0, 8).map((edge) => `<span>${escapeHtml(edge.relation)}</span>`).join("") || "<span>isolated</span>"}
    </div>
    <details class="brain-payload">
      <summary>Raw record preview</summary>
      <pre>${escapeHtml(payloadPreview.slice(0, 2800))}</pre>
    </details>
  `;
}

function drawBrainCanvas(canvas, graph, positioned, width, height) {
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  canvas.style.height = `${height}px`;
  canvas.style.width = "100%";
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const cx = width / 2;
  const cy = height / 2;
  const tick = Date.now() / 1000;
  const selected = state.selectedBrainNodeId;
  state.brainHitTargets = [];

  const bg = ctx.createRadialGradient(cx, cy, 24, cx, cy, Math.max(width, height) * 0.72);
  bg.addColorStop(0, "rgba(73,58,118,0.24)");
  bg.addColorStop(0.42, "rgba(17,20,30,0.66)");
  bg.addColorStop(1, "rgba(8,8,10,1)");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, width, height);

  ctx.save();
  ctx.translate(cx, cy);
  for (let index = 0; index < 8; index += 1) {
    const radiusX = 95 + index * 120;
    const radiusY = 48 + index * 70;
    ctx.beginPath();
    ctx.ellipse(0, 0, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(168,139,250,${0.075 - index * 0.006})`;
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  for (let ray = 0; ray < 28; ray += 1) {
    const angle = (ray / 28) * Math.PI * 2 + tick * 0.006;
    ctx.beginPath();
    ctx.moveTo(Math.cos(angle) * 38, Math.sin(angle) * 18);
    ctx.lineTo(Math.cos(angle) * width, Math.sin(angle) * height);
    ctx.strokeStyle = "rgba(168,139,250,0.024)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  ctx.restore();

  for (let index = 0; index < 105; index += 1) {
    const x = seededUnit(index, "star-x") * width;
    const y = seededUnit(index, "star-y") * height;
    const alpha = 0.025 + seededUnit(index, "star-a") * 0.11;
    const size = 0.35 + seededUnit(index, "star-s") * 1.1;
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(226,232,255,${alpha})`;
    ctx.fill();
  }

  const edges = [...(graph.edges || [])].sort((left, right) => {
    const l = ((positioned.get(left.source)?.depthScale || 1) + (positioned.get(left.target)?.depthScale || 1)) / 2;
    const r = ((positioned.get(right.source)?.depthScale || 1) + (positioned.get(right.target)?.depthScale || 1)) / 2;
    return l - r;
  });
  for (const edge of edges) {
    const source = positioned.get(edge.source);
    const target = positioned.get(edge.target);
    if (!source || !target) continue;
    const active = selected && (edge.source === selected || edge.target === selected);
    const depth = (source.depthScale + target.depthScale) / 2;
    const alpha = active ? 0.72 : Math.max(0.025, Math.min(0.16, depth * Number(edge.weight || 0.6) * 0.095));
    const gradient = ctx.createLinearGradient(source.x, source.y, target.x, target.y);
    gradient.addColorStop(0, active ? "rgba(223,214,255,0.95)" : `rgba(132,165,255,${alpha})`);
    gradient.addColorStop(0.5, active ? "rgba(168,139,250,0.98)" : `rgba(168,139,250,${alpha * 1.3})`);
    gradient.addColorStop(1, active ? "rgba(223,214,255,0.95)" : `rgba(79,209,197,${alpha})`);
    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    const mx = (source.x + target.x) / 2 + (target.y - source.y) * 0.035;
    const my = (source.y + target.y) / 2 - (target.x - source.x) * 0.035;
    ctx.quadraticCurveTo(mx, my, target.x, target.y);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = active ? 2.15 : Math.max(0.32, depth * Number(edge.weight || 1) * 0.46);
    ctx.shadowBlur = active ? 14 : 3;
    ctx.shadowColor = active ? "rgba(168,139,250,0.72)" : "rgba(168,139,250,0.16)";
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  const nodes = Array.from(positioned.values()).sort((left, right) => left.depthScale - right.depthScale);
  for (const node of nodes) {
    const active = node.id === selected;
    const connected = selected && (graph.edges || []).some((edge) => (edge.source === selected && edge.target === node.id) || (edge.target === selected && edge.source === node.id));
    const drift = Math.sin(tick * 0.35 + seededAngle(node.id)) * (active ? 1.2 : 2.8);
    const x = node.x + Math.cos(seededAngle(node.id) + tick * 0.08) * drift;
    const y = node.y + Math.sin(seededAngle(node.id) + tick * 0.06) * drift;
    const radius = brainNodeRadius(node) * node.depthScale * (active ? 1.12 : 0.92);
    const color = brainNodeColor(node.group);
    const alpha = active ? 0.98 : connected ? 0.82 : node.depthOpacity * 0.7;
    const halo = ctx.createRadialGradient(x, y, radius * 0.2, x, y, radius * 2.65);
    halo.addColorStop(0, hexToRgba(color, active ? 0.28 : 0.16));
    halo.addColorStop(1, "rgba(0,0,0,0)");
    ctx.beginPath();
    ctx.fillStyle = halo;
    ctx.arc(x, y, radius * 2.65, 0, Math.PI * 2);
    ctx.fill();

    const orb = ctx.createRadialGradient(x - radius * 0.35, y - radius * 0.42, radius * 0.1, x, y, radius);
    orb.addColorStop(0, "rgba(255,255,255,0.76)");
    orb.addColorStop(0.24, color);
    orb.addColorStop(1, "rgba(28,23,42,0.92)");
    ctx.beginPath();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = orb;
    ctx.shadowBlur = active ? 20 : 6 * node.depthScale;
    ctx.shadowColor = color;
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = active ? "rgba(255,255,255,0.82)" : "rgba(255,255,255,0.16)";
    ctx.lineWidth = active ? 1.5 : 0.55;
    ctx.stroke();
    ctx.globalAlpha = 1;

    state.brainHitTargets.push({ id: node.id, x, y, r: Math.max(radius + 8, 16) });

    const showLabel = active || connected || node.group === "agent" || (node.group === "project" && node.depthScale > 0.82);
    if (showLabel) {
      ctx.font = `${active ? 700 : 600} ${Math.max(9, Math.min(12, 9.2 * node.depthScale))}px "Avenir Next", "Segoe UI", sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.lineWidth = 4;
      ctx.strokeStyle = "rgba(8,8,10,0.82)";
      ctx.fillStyle = active ? "rgba(255,255,255,0.96)" : "rgba(226,232,255,0.7)";
      const label = node.label.length > 26 ? `${node.label.slice(0, 25)}…` : node.label;
      ctx.strokeText(label, x, y + radius + 6);
      ctx.fillText(label, x, y + radius + 6);
    }
  }
}

function renderBrainGraph() {
  const graph = filteredBrainGraph();
  if (!elements.brainGraphCanvas) {
    return;
  }
  renderBrainStats(state.brainGraph);
  renderBrainLegend(state.brainGraph);
  renderBrainVault(state.brainGraph);
  const visibleGraph = visibleBrainGraph(graph);
  if (!visibleGraph.nodes?.length) {
    elements.brainGraphCanvas.innerHTML = `
      <article class="empty-state">
        <strong>No brain records match.</strong>
        <p class="meta">Clear the filter or seed memory to populate the graph.</p>
      </article>
    `;
    renderBrainInspector("");
    return;
  }
  const canvasRect = elements.brainGraphCanvas.getBoundingClientRect();
  const pageWidth = elements.brainPage?.hidden === false ? window.innerWidth - 340 : window.innerWidth - 520;
  const width = Math.max(900, Math.round(canvasRect.width || pageWidth || 980));
  const height = Math.max(680, Math.min(980, Math.round(window.innerHeight * (elements.brainPage?.hidden === false ? 0.78 : 0.66))));
  const positioned = positionedBrainNodes(visibleGraph.nodes, visibleGraph.edges, width, height);
  elements.brainGraphCanvas.innerHTML = `
    <canvas id="brain-canvas" class="brain-canvas" width="${width}" height="${height}" aria-label="3D Hermes memory and synapse field"></canvas>
    <div class="brain-field-hud">
      <strong>${visibleGraph.nodes.length}</strong> rendered
      ${visibleGraph.hiddenCount ? `<span>${visibleGraph.hiddenCount} dimmed</span>` : ""}
    </div>
  `;
  const canvas = elements.brainGraphCanvas.querySelector("#brain-canvas");
  if (canvas) {
    drawBrainCanvas(canvas, visibleGraph, positioned, width, height);
    setTimeout(() => {
      if (currentRoute() === "brain" && elements.brainGraphCanvas?.querySelector("#brain-canvas") === canvas) {
        drawBrainCanvas(canvas, visibleGraph, positioned, width, height);
      }
    }, 650);
  }
  renderBrainInspector(state.selectedBrainNodeId);
}

async function loadBrainGraph() {
  try {
    state.brainGraph = await fetchJson("/api/brain-graph?cognitive_limit=28");
    if (!state.selectedBrainNodeId && state.brainGraph.nodes?.length) {
      const sheldon = state.brainGraph.nodes.find((node) => node.id === "agent:sheldon");
      state.selectedBrainNodeId = sheldon?.id || state.brainGraph.nodes[0].id;
    }
    renderBrainGraph();
  } catch (error) {
    console.error(error);
    if (elements.brainGraphCanvas) {
      elements.brainGraphCanvas.innerHTML = `
        <article class="empty-state">
          <strong>Brain graph failed to load.</strong>
          <p class="meta">${escapeHtml(String(error.message || error))}</p>
        </article>
      `;
    }
  }
}

async function focusProject(projectId) {
  await fetchJson("/api/projects/activate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      reason: "Focused from the Hermes v2 sample-aligned deck.",
    }),
  });
}

async function archiveProject(projectId) {
  await fetchJson("/api/projects/archive", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      reason: "Archived from the Hermes v2 sample-aligned deck.",
    }),
  });
}

async function loadDashboard() {
  if (state.loading) {
    return;
  }
  state.loading = true;
  elements.refreshButton.disabled = true;

  try {
    const [snapshotPayload, runsPayload, dispatchesPayload, alertsPayload, brainPayload, truthLoopPayload, realityPayload, repairPayload] = await Promise.all([
      fetchJson("/api/bootstrap"),
      fetchJson("/api/runs?limit=24"),
      fetchJson("/api/dispatches?limit=24"),
      fetchJson("/api/monitor?limit=24"),
      fetchJson("/api/brain-graph?cognitive_limit=28"),
      fetchJson("/api/truth-loop?limit=12"),
      fetchJson("/api/reality-layer?limit=12"),
      fetchJson("/api/repair-bay?limit=12"),
    ]);

    state.snapshot = snapshotPayload;
    state.runs = runsPayload.runs || [];
    state.dispatches = dispatchesPayload.dispatches || [];
    state.alerts = alertsPayload.alerts || [];
    state.brainGraph = brainPayload;
    state.truthLoop = truthLoopPayload;
    state.realityLayer = realityPayload;
    state.repairBay = repairPayload;
    if (!state.selectedBrainNodeId && state.brainGraph.nodes?.length) {
      const sheldon = state.brainGraph.nodes.find((node) => node.id === "agent:sheldon");
      state.selectedBrainNodeId = sheldon?.id || state.brainGraph.nodes[0].id;
    }

    renderHeader();
    renderHero();
    renderProjects();
    renderQueue();
    renderAgents();
    renderTheater();
    renderRadar();
    renderTruthLoop();
    renderRealityLayer();
    renderRepairBay();
    renderActivity();
    renderBrainGraph();
    applyRoute();
  } catch (error) {
    console.error(error);
    elements.operatorPresence.textContent = "Command deck failed to load";
    elements.operatorSubtitle.textContent = String(error.message || error);
  } finally {
    state.loading = false;
    elements.refreshButton.disabled = false;
  }
}

async function submitRealityCapture(event) {
  event.preventDefault();
  if (state.realityCaptureRunning) {
    return;
  }
  const note = String(elements.realityNote?.value || "").trim();
  const file = elements.realityFile?.files?.[0];
  if (!note && !file) {
    setRealityStatus("Add note or image", "error");
    elements.realityNote?.focus();
    return;
  }
  state.realityCaptureRunning = true;
  setRealityStatus("Capturing", "busy");
  if (elements.realitySubmit) {
    elements.realitySubmit.disabled = true;
    elements.realitySubmit.textContent = "Capturing...";
  }
  try {
    const attachments = [];
    if (file) {
      attachments.push({
        name: file.name || "field-image",
        data_url: await readFileAsDataUrl(file),
      });
    }
    const payload = await fetchJson("/api/reality-layer/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: activeProjectId(),
        mode: elements.realityMode?.value || "field",
        note,
        source: "operator-portal",
        attachments,
      }),
    });
    state.realityLayer = payload.snapshot || state.realityLayer;
    state.repairBay = payload.repair_bay || state.repairBay;
    elements.realityForm?.reset();
    setRealityStatus("Routed", "ready");
    await loadDashboard();
  } catch (error) {
    console.error(error);
    setRealityStatus("Capture failed", "error");
    if (elements.realityView) {
      elements.realityView.innerHTML = `
        <article class="reality-empty error">
          <strong>Capture failed.</strong>
          <p>${escapeHtml(String(error.message || error))}</p>
        </article>
      `;
    }
  } finally {
    state.realityCaptureRunning = false;
    if (elements.realitySubmit) {
      elements.realitySubmit.disabled = false;
      elements.realitySubmit.textContent = "Capture";
    }
  }
}

async function runRepairDiagnostics(repairId) {
  if (!repairId || state.repairRunning) {
    return;
  }
  state.repairRunning = true;
  try {
    const payload = await fetchJson("/api/repair-bay/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repair_id: repairId }),
    });
    state.repairBay = payload.snapshot || state.repairBay;
    renderRepairBay();
    renderActivity();
  } catch (error) {
    console.error(error);
  } finally {
    state.repairRunning = false;
  }
}

async function runTruthLoop() {
  if (state.truthLoopRunning) {
    return;
  }
  state.truthLoopRunning = true;
  if (elements.truthLoopRun) {
    elements.truthLoopRun.disabled = true;
    elements.truthLoopRun.textContent = "Running...";
  }
  try {
    const payload = await fetchJson("/api/truth-loop/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ focus: "operator truth loop" }),
    });
    state.truthLoop = payload.snapshot || state.truthLoop;
    await loadDashboard();
  } catch (error) {
    console.error(error);
    if (elements.truthLoopView) {
      elements.truthLoopView.innerHTML = `
        <article class="truth-loop-empty error">
          <strong>Truth Loop failed.</strong>
          <p>${escapeHtml(String(error.message || error))}</p>
        </article>
      `;
    }
  } finally {
    state.truthLoopRunning = false;
    if (elements.truthLoopRun) {
      elements.truthLoopRun.disabled = false;
      elements.truthLoopRun.textContent = "Run Loop";
    }
  }
}

async function handleProjectAction(event) {
  const target = event.target.closest("[data-action]");
  if (!target) {
    return;
  }

  const { action, projectId } = target.dataset;
  if (!projectId) {
    return;
  }

  try {
    target.disabled = true;
    if (action === "focus") {
      await focusProject(projectId);
    } else if (action === "archive") {
      const confirmed = window.confirm(`Archive ${projectId}?`);
      if (!confirmed) {
        return;
      }
      await archiveProject(projectId);
    }
    await loadDashboard();
  } catch (error) {
    window.alert(String(error.message || error));
  } finally {
    target.disabled = false;
  }
}

elements.refreshButton.addEventListener("click", () => {
  loadDashboard();
});

elements.truthLoopRun?.addEventListener("click", runTruthLoop);
elements.realityForm?.addEventListener("submit", submitRealityCapture);
elements.repairView?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-repair-run]");
  if (!button) {
    return;
  }
  runRepairDiagnostics(button.dataset.repairRun || "");
});
window.addEventListener("hashchange", applyRoute);
window.addEventListener("resize", () => {
  if (currentRoute() === "brain") {
    window.requestAnimationFrame(renderBrainGraph);
  }
});
elements.activeProjects.addEventListener("click", handleProjectAction);
elements.blockedPill?.addEventListener("click", () => {
  setBlockedDetailsOpen(elements.blockedDetails?.hidden !== false);
});
elements.blockedClose?.addEventListener("click", () => {
  setBlockedDetailsOpen(false);
});
elements.blockedList?.addEventListener("click", handleProjectAction);
elements.brainRefresh?.addEventListener("click", loadBrainGraph);
elements.brainSearch?.addEventListener("input", renderBrainGraph);
elements.brainGroupFilters?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-brain-group]");
  if (!button) {
    return;
  }
  state.brainGroupFilter = button.dataset.brainGroup || "all";
  renderBrainGraph();
});
elements.brainTableList?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-table-query]");
  if (!button || !elements.brainSearch) {
    return;
  }
  elements.brainSearch.value = button.dataset.tableQuery || "";
  state.brainGroupFilter = "all";
  renderBrainGraph();
});
elements.brainGraphCanvas?.addEventListener("click", (event) => {
  const canvas = event.target.closest("#brain-canvas");
  if (!canvas) {
    return;
  }
  const rect = canvas.getBoundingClientRect();
  const scaleX = Number(canvas.getAttribute("width") || rect.width) / rect.width;
  const scaleY = Number(canvas.getAttribute("height") || rect.height) / rect.height;
  const x = (event.clientX - rect.left) * scaleX;
  const y = (event.clientY - rect.top) * scaleY;
  const hit = [...state.brainHitTargets]
    .reverse()
    .find((target) => {
      const dx = target.x - x;
      const dy = target.y - y;
      return Math.sqrt(dx * dx + dy * dy) <= target.r;
    });
  if (!hit) {
    return;
  }
  state.selectedBrainNodeId = hit.id;
  renderBrainGraph();
});
elements.chatForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  sendChatMessage(elements.chatInput?.value || "");
});
elements.chatInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.chatForm?.requestSubmit();
  }
});
elements.floatingChatToggle?.addEventListener("click", toggleFloatingChat);
elements.floatingChatClose?.addEventListener("click", closeFloatingChat);
elements.floatingChatForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  sendChatMessage(elements.floatingChatInput?.value || "");
});
for (const button of elements.voiceToggles) {
  button.addEventListener("click", toggleVoiceMode);
}
elements.floatingChatInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.floatingChatForm?.requestSubmit();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeFloatingChat();
  }
});

loadDashboard();
applyRoute();
initVoiceMode();
