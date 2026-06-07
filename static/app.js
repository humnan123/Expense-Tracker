const API = "";
const token = () => localStorage.getItem("token");
const headers = () => ({ "Authorization": `Bearer ${token()}`, "Content-Type": "application/json" });

if (!token()) window.location.href = "/static/index.html";

let pieChart = null;
let barChart = null;
let categoriesMap = {};

window.onload = () => {
  const now = new Date();
  const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  document.getElementById("month-picker").value = month;
  loadCategories();
  loadAll();
};

function logout() {
  localStorage.removeItem("token");
  window.location.href = "/static/index.html";
}

function clearMonth() {
  document.getElementById("month-picker").value = "";
  loadAll();
}

async function loadAll() {
  await loadSummary();
  await loadTransactions();
}

async function loadCategories() {
  const res = await fetch(`${API}/categories`, { headers: headers() });
  const cats = await res.json();
  cats.forEach(c => categoriesMap[c.id] = c.name);
  const sel = document.getElementById("category");
  sel.innerHTML = cats.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
}

async function loadSummary() {
  const month = document.getElementById("month-picker").value;
  const monthParam = month ? `?month=${month}` : "";
  const res = await fetch(`${API}/transactions/summary${monthParam}`, { headers: headers() });
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById("total-income").textContent = data.income.toLocaleString();
  document.getElementById("total-expenses").textContent = data.expenses.toLocaleString();
  document.getElementById("balance").textContent = (data.income - data.expenses).toLocaleString();

  const labels = data.by_category.map(c => c.category);
  const values = data.by_category.map(c => c.total);
  const colors = ["#4f46e5","#16a34a","#dc2626","#f59e0b","#06b6d4","#ec4899"];

  if (pieChart) pieChart.destroy();
  pieChart = new Chart(document.getElementById("pie-chart"), {
    type: "pie",
    data: { labels, datasets: [{ data: values, backgroundColor: colors }] },
    options: { plugins: { legend: { position: "bottom" } } }
  });

  if (barChart) barChart.destroy();
  barChart = new Chart(document.getElementById("bar-chart"), {
    type: "bar",
    data: {
      labels: ["Selected period"],
      datasets: [
        { label: "Income", data: [data.income], backgroundColor: "#16a34a" },
        { label: "Expenses", data: [data.expenses], backgroundColor: "#dc2626" }
      ]
    },
    options: { plugins: { legend: { position: "bottom" } } }
  });
}

async function loadTransactions() {
  const month = document.getElementById("month-picker").value;
  const monthParam = month ? `?month=${month}` : "";
  const res = await fetch(`${API}/transactions${monthParam}`, { headers: headers() });
  const data = await res.json();
  const body = document.getElementById("transactions-body");
  body.innerHTML = data.map(t => `
    <tr>
      <td>${t.date}</td>
      <td>${t.description}</td>
      <td>${categoriesMap[t.category_id] || t.category_id}</td>
      <td><span class="badge badge-${t.type}">${t.type}</span></td>
      <td>${t.amount.toLocaleString()}</td>
      <td><button class="del-btn" onclick="deleteTransaction(${t.id})">Delete</button></td>
    </tr>
  `).join("");
}

async function addTransaction() {
  const body = {
    amount: parseFloat(document.getElementById("amount").value),
    description: document.getElementById("description").value,
    type: document.getElementById("type").value,
    category_id: parseInt(document.getElementById("category").value),
    date: document.getElementById("date").value
  };
  const params = new URLSearchParams(body).toString();
  await fetch(`${API}/transactions?${params}`, { method: "POST", headers: headers() });
  loadAll();
}

async function deleteTransaction(id) {
  await fetch(`${API}/transactions/${id}`, { method: "DELETE", headers: headers() });
  loadAll();
}