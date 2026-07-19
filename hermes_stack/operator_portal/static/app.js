const state = {
  snapshot: null,
  runs: [],
  dispatches: [],
  alerts: [],
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
  floatingVoiceToggle: document.querySelector("#floating-voice-toggle"),
  queueTable: document.querySelector("#queue-table"),
  agentTeam: document.querySelector("#agent-team"),
  agentTheater: document.querySelector("#agent-theater"),
  agentRadar: document.querySelector("#agent-radar"),
  activityFeed: document.querySelector("#activity-feed"),
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
  if (!elements.floatingVoiceToggle) {
    return;
  }
  elements.floatingVoiceToggle.setAttribute("aria-pressed", listening ? "true" : "false");
  elements.floatingVoiceToggle.textContent = listening ? "Listening..." : "Voice";
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
  if (!elements.floatingVoiceToggle) {
    return;
  }
  if (!state.voiceSupported) {
    elements.floatingVoiceToggle.disabled = true;
    elements.floatingVoiceToggle.textContent = "No Voice";
    elements.floatingVoiceToggle.title = "This browser does not expose speech recognition and speech synthesis.";
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

function buildActivityFeed() {
  const activities = [];
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
    const [snapshotPayload, runsPayload, dispatchesPayload, alertsPayload] = await Promise.all([
      fetchJson("/api/bootstrap"),
      fetchJson("/api/runs?limit=24"),
      fetchJson("/api/dispatches?limit=24"),
      fetchJson("/api/monitor?limit=24"),
    ]);

    state.snapshot = snapshotPayload;
    state.runs = runsPayload.runs || [];
    state.dispatches = dispatchesPayload.dispatches || [];
    state.alerts = alertsPayload.alerts || [];

    renderHeader();
    renderHero();
    renderProjects();
    renderQueue();
    renderAgents();
    renderTheater();
    renderRadar();
    renderActivity();
  } catch (error) {
    console.error(error);
    elements.operatorPresence.textContent = "Command deck failed to load";
    elements.operatorSubtitle.textContent = String(error.message || error);
  } finally {
    state.loading = false;
    elements.refreshButton.disabled = false;
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
elements.activeProjects.addEventListener("click", handleProjectAction);
elements.blockedPill?.addEventListener("click", () => {
  setBlockedDetailsOpen(elements.blockedDetails?.hidden !== false);
});
elements.blockedClose?.addEventListener("click", () => {
  setBlockedDetailsOpen(false);
});
elements.blockedList?.addEventListener("click", handleProjectAction);
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
elements.floatingVoiceToggle?.addEventListener("click", toggleVoiceMode);
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
initVoiceMode();
