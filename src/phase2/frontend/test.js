const $ = (id) => document.getElementById(id);

async function loadRec() {
  const userId = $("user-id").value.trim() || "user_001";
  const res = await fetch("/api/v1/recommendations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  $("result").textContent = JSON.stringify(await res.json(), null, 2);
}

$("refresh-btn").onclick = loadRec;
$("dashboard-btn").onclick = async () => {
  const res = await fetch("/api/v1/phase3/analytics/dashboard");
  $("extra").textContent = JSON.stringify(await res.json(), null, 2);
};
$("monitor-btn").onclick = async () => {
  const res = await fetch("/api/v1/phase4/monitoring/status");
  $("extra").textContent = JSON.stringify(await res.json(), null, 2);
};

loadRec();
