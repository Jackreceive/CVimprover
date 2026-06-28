const sessionStore = window.sessionStorage;

const api = {
  token: sessionStore.getItem("aim_token") || "",
  user: safeJsonParse(sessionStore.getItem("aim_user")),
};

const state = {
  authMode: "login",
  resumes: [],
  jobs: [],
  matches: [],
  applications: [],
  currentMatch: null,
};

const labels = {
  wishlist: "待投递",
  applied: "已投递",
  interviewing: "面试中",
  offer: "Offer",
  rejected: "已拒绝",
};

const statusOrder = ["wishlist", "applied", "interviewing", "offer", "rejected"];

const $ = (id) => document.getElementById(id);

const matchLabels = {
  pending: "排队中",
  processing: "分析中",
  completed: "已完成",
  failed: "分析失败",
};

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeJsonParse(value) {
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

function clearSession() {
  api.token = "";
  api.user = null;
  sessionStore.removeItem("aim_token");
  sessionStore.removeItem("aim_user");
  localStorage.removeItem("aim_token");
  localStorage.removeItem("aim_user");
}

function optionHtml(value, label, selected = false) {
  return `<option value="${escapeHtml(value)}" ${selected ? "selected" : ""}>${escapeHtml(label)}</option>`;
}

function listHtml(items, emptyText) {
  if (!items?.length) return `<li class="empty-list">${escapeHtml(emptyText)}</li>`;
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function setMessage(id, text, isError = true) {
  const el = $(id);
  el.textContent = text || "";
  el.style.color = isError ? "var(--red)" : "var(--green)";
}

async function request(path, options = {}) {
  const headers = options.headers || {};
  if (api.token) headers.Authorization = `Bearer ${api.token}`;
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";

  const response = await fetch(`/api${path}`, { ...options, headers });
  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text || "服务返回了非 JSON 响应" };
  }
  if (!response.ok) throw new Error(data?.detail || "请求失败");
  return data;
}

function showApp() {
  $("authView").classList.add("hidden");
  $("appView").classList.remove("hidden");
  $("userLabel").textContent = api.user?.email || "";
}

function showAuth() {
  $("appView").classList.add("hidden");
  $("authView").classList.remove("hidden");
  $("userLabel").textContent = "";
  setMessage("toast", "");
}

function setAuthMode(mode) {
  state.authMode = mode;
  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.authMode === mode);
  });
  document.querySelectorAll(".register-only").forEach((el) => el.classList.toggle("hidden", mode !== "register"));
  $("authSubmit").textContent = mode === "login" ? "登录" : "注册";
}

function renderSelects() {
  $("resumeCount").textContent = state.resumes.length;
  $("jobCount").textContent = state.jobs.length;
  $("resumeSelect").innerHTML = state.resumes.length
    ? state.resumes.map((resume) => optionHtml(resume.id, resume.filename)).join("")
    : optionHtml("", "先上传一份 PDF 简历");
  $("jobSelect").innerHTML = state.jobs.length
    ? state.jobs.map((job) => optionHtml(job.id, `${job.company ? `${job.company} · ` : ""}${job.title}`)).join("")
    : optionHtml("", "先保存一个岗位 JD");
}

function renderMetrics() {
  const stats = statusOrder.map((status) => ({
    label: labels[status],
    value: state.applications.filter((item) => item.status === status).length,
  }));
  const completed = state.matches.filter((match) => match.status === "completed");
  const avg = completed.length
    ? Math.round(completed.reduce((sum, match) => sum + (match.score || 0), 0) / completed.length)
    : 0;
  const metrics = [{ label: "平均匹配", value: `${avg}%` }, ...stats];
  $("metrics").innerHTML = metrics
    .map((metric) => `<div class="metric"><strong>${escapeHtml(metric.value)}</strong><span>${escapeHtml(metric.label)}</span></div>`)
    .join("");
}

function renderResult(match) {
  state.currentMatch = match;
  const score = match?.score ?? null;
  $("matchState").textContent = match ? matchLabels[match.status] || match.status : "待分析";
  $("scoreText").textContent = score === null ? "--" : `${score}%`;
  $("scoreRing").style.background = `conic-gradient(var(--green) ${score ? score * 3.6 : 0}deg, #e6edf4 0deg)`;
  $("summaryText").textContent = match?.summary || match?.error_message || "暂无分析结果";
  $("gapList").innerHTML = listHtml(match?.skill_gaps, "分析完成后显示技能差距");
  $("suggestionList").innerHTML = listHtml(match?.resume_suggestions, "分析完成后显示修改建议");
}

function renderKanban() {
  $("kanban").innerHTML = statusOrder
    .map((status) => {
      const cards = state.applications.filter((item) => item.status === status);
      return `
        <section class="column">
          <h3>${escapeHtml(labels[status])} <span>${cards.length}</span></h3>
          ${cards
            .map(
              (item) => `
              <article class="application-card">
                <strong>${escapeHtml(item.job?.title || "未命名岗位")}</strong>
                <p>${escapeHtml(item.job?.company || "未填写公司")}${item.match?.score ? ` · 匹配 ${escapeHtml(item.match.score)}%` : ""}</p>
                <p>${escapeHtml(item.notes || "暂无备注")}</p>
                <select data-application-id="${item.id}">
                  ${statusOrder.map((option) => optionHtml(option, labels[option], option === item.status)).join("")}
                </select>
              </article>
            `
            )
            .join("") || '<div class="empty-card">暂无投递</div>'}
        </section>
      `;
    })
    .join("");

  document.querySelectorAll("[data-application-id]").forEach((select) => {
    select.addEventListener("change", async (event) => {
      const id = event.target.dataset.applicationId;
      await request(`/applications/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: event.target.value }),
      });
      await refreshAll();
      setMessage("toast", "状态已更新", false);
    });
  });
}

async function refreshAll() {
  const [resumes, jobs, matches, applications] = await Promise.all([
    request("/resumes"),
    request("/jobs"),
    request("/matches"),
    request("/applications"),
  ]);
  state.resumes = resumes;
  state.jobs = jobs;
  state.matches = matches;
  state.applications = applications;
  renderSelects();
  renderMetrics();
  renderKanban();
  if (!state.currentMatch && matches[0]) renderResult(matches[0]);
}

async function pollMatch(id) {
  const timer = setInterval(async () => {
    try {
      const match = await request(`/matches/${id}`);
      renderResult(match);
      if (["completed", "failed"].includes(match.status)) {
        clearInterval(timer);
        await refreshAll();
      }
    } catch (error) {
      clearInterval(timer);
      setMessage("toast", error.message);
    }
  }, 1800);
}

document.querySelectorAll("[data-auth-mode]").forEach((button) => {
  button.addEventListener("click", () => setAuthMode(button.dataset.authMode));
});

$("authForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("authMessage", "");
  const payload = {
    email: $("email").value,
    password: $("password").value,
    full_name: $("fullName").value,
  };
  try {
    const result = await request(`/auth/${state.authMode}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    api.token = result.access_token;
    api.user = result.user;
    sessionStore.setItem("aim_token", api.token);
    sessionStore.setItem("aim_user", JSON.stringify(api.user));
    showApp();
    await refreshAll();
  } catch (error) {
    setMessage("authMessage", error.message);
  }
});

$("logoutBtn").addEventListener("click", () => {
  clearSession();
  showAuth();
});

$("resumeForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("resumeFile").files[0];
  const form = new FormData();
  form.append("file", file);
  await request("/resumes", { method: "POST", body: form });
  $("resumeFile").value = "";
  await refreshAll();
});

$("resumeFile").addEventListener("change", (event) => {
  const file = event.target.files[0];
  $("resumeFileLabel").textContent = file?.name || "选择 PDF";
});

$("jobForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  await request("/jobs", {
    method: "POST",
    body: JSON.stringify({
      title: $("jobTitle").value,
      company: $("company").value,
      content: $("jobContent").value,
    }),
  });
  event.target.reset();
  await refreshAll();
});

$("matchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const resumeId = Number($("resumeSelect").value);
  const jobId = Number($("jobSelect").value);
  if (!resumeId || !jobId) {
    setMessage("toast", "请先上传简历并保存 JD");
    return;
  }
  const match = await request("/matches", {
    method: "POST",
    body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
  });
  renderResult(match);
  pollMatch(match.id);
});

$("saveApplicationBtn").addEventListener("click", async () => {
  if (!state.currentMatch) {
    setMessage("toast", "请先完成一次匹配分析");
    return;
  }
  await request("/applications", {
    method: "POST",
    body: JSON.stringify({
      job_id: state.currentMatch.job_id,
      match_id: state.currentMatch.id,
      status: "wishlist",
      notes: state.currentMatch.summary,
    }),
  });
  await refreshAll();
  setMessage("toast", "投递记录已保存", false);
});

async function bootstrapSession() {
  showAuth();
  localStorage.removeItem("aim_token");
  localStorage.removeItem("aim_user");
  if (!api.token) return;

  try {
    api.user = await request("/auth/me");
    sessionStore.setItem("aim_user", JSON.stringify(api.user));
    showApp();
    await refreshAll();
  } catch {
    clearSession();
    showAuth();
  }
}

bootstrapSession();
