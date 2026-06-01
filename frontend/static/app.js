const rootsEl = document.querySelector("#roots");
const statusEl = document.querySelector("#status");
const inspectionEl = document.querySelector("#inspection");
const generateForm = document.querySelector("#generate-form");
const validateForm = document.querySelector("#validate-form");

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function sampleText(root) {
  if (!root.sample?.result) return "屈折样例: --";
  return `屈折样例: ${root.sample.result}`;
}

function renderRootCard(root) {
  const card = el("div", "root-card");
  card.tabIndex = 0;
  card.append(el("div", "root-word", root.base));

  const meta = el("div", "meta-row");
  [root.pos, root.inflection ?? "unknown", root.subtype ?? "-", `${root.score}`].forEach((item) => {
    meta.append(el("span", "chip", item));
  });
  card.append(meta);
  card.append(el("div", "sample", sampleText(root)));
  card.addEventListener("click", () => renderInspection(root));
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") renderInspection(root);
  });
  return card;
}

function renderRoots(roots) {
  rootsEl.replaceChildren(...roots.map(renderRootCard));
  statusEl.textContent = `${roots.length} roots`;
  if (roots[0]) renderInspection(roots[0]);
}

function renderInspection(root) {
  inspectionEl.className = "inspection";
  const title = el("div", "analysis-word", root.base);
  const state = el("div", root.valid ? "ok" : "bad", root.valid ? "合法" : "不合法");
  const meta = el("div", "meta-row");
  [
    `POS ${root.pos}`,
    `Type ${root.inflection ?? "-"}`,
    `Subtype ${root.subtype ?? "-"}`,
    `Score ${root.score}`,
    `Tokens ${root.tokens.join(" ")}`,
  ].forEach((item) => meta.append(el("span", "chip", item)));

  const reason = el("p", "", root.reason);
  const sample = el("p", "sample", sampleText(root));
  const list = el("ul", "diagnostics");
  const diagnostics = root.diagnostics.length ? root.diagnostics : ["No diagnostics."];
  diagnostics.forEach((item) => list.append(el("li", "", item)));
  inspectionEl.replaceChildren(title, state, meta, reason, sample, list);
}

generateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(generateForm);
  statusEl.textContent = "Generating";
  const payload = {
    pos: form.get("pos") || null,
    count: Number(form.get("count") || 12),
  };
  try {
    const data = await postJson("/api/generate", payload);
    renderRoots(data.roots);
  } catch (error) {
    statusEl.textContent = "Error";
    inspectionEl.className = "inspection";
    inspectionEl.replaceChildren(el("p", "bad", error instanceof Error ? error.message : String(error)));
  }
});

validateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(validateForm);
  const word = String(form.get("word") || "").trim();
  if (!word) return;
  const data = await postJson("/api/validate", {
    word,
    pos: form.get("validate-pos") || "noun",
  });
  renderInspection(data);
});

postJson("/api/generate", { count: 12, pos: null }).then((data) => {
  renderRoots(data.roots);
});
