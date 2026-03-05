// -------------------------------
// FETCH HELPER
// -------------------------------
async function apiGet(url) {
    const res = await fetch(url);
    return await res.json();
}

// Auto-refresh every 5 seconds
setInterval(() => {
    loadDashboard();
}, 5000);


// -------------------------------
// MAIN LOADER
// -------------------------------
async function loadDashboard() {
    updateOverallStats();
    updateTopWords();
    updateRecentComments();
    updateTrendChart();
    updateDistributionChart();
}

document.addEventListener("DOMContentLoaded", loadDashboard);


// -------------------------------
// 1. OVERALL STATS
// -------------------------------
async function updateOverallStats() {
    const stats = await apiGet("/api/stats");

    document.getElementById("totalComments").innerText = stats.total_comments;
    document.getElementById("toxicityRatio").innerText = stats.toxicity_ratio + "%";

    // Spike status
    const full = await apiGet("/api/analytics");
    const spike = full.spike;

    if (spike.spike) {
        document.getElementById("spikeInfo").innerHTML =
            `<span class="text-red-400">⚠ Spike Detected (+${spike.percent_increase}%)</span>`;
    } else {
        document.getElementById("spikeInfo").innerHTML =
            `<span class="text-green-400">No Spike</span>`;
    }
}


// -------------------------------
// 2. TOP WORDS
// -------------------------------
async function updateTopWords() {
    const words = await apiGet("/api/words");
    const ul = document.getElementById("wordList");
    ul.innerHTML = "";

    words.forEach(([word, freq]) => {
        ul.innerHTML += `
            <li class="glass p-2 rounded-lg text-white">
                ${word} <span class="text-blue-300">(${freq})</span>
            </li>
        `;
    });
}


// -------------------------------
// 3. RECENT COMMENTS
// -------------------------------
async function updateRecentComments() {
    const comments = await apiGet("/api/comments");
    const ul = document.getElementById("recentComments");
    ul.innerHTML = "";

    comments.forEach(([text, decision, time]) => {
        ul.innerHTML += `
            <li class="glass p-3 rounded-xl">
                <p class="text-sm">${text}</p>
                <p class="text-xs text-gray-300 mt-1">
                    Decision: <span class="text-yellow-300">${decision}</span>
                    | <span class="text-gray-400">${time}</span>
                </p>
            </li>
        `;
    });
}


// -------------------------------
// 4. TREND CHART (Hourly Toxicity)
// -------------------------------
let trendChart = null;

async function updateTrendChart() {
    const trend = await apiGet("/api/trend");

    const labels = Object.keys(trend).reverse();
    const values = labels.map(k => trend[k].avg_toxicity);

    const ctx = document.getElementById("trendChart").getContext("2d");

    if (trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Average Toxicity",
                data: values,
                borderWidth: 2,
                borderColor: "rgb(59,130,246)",
                fill: false,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}


// -------------------------------
// 5. TOXICITY DISTRIBUTION CHART
// -------------------------------
let distChart = null;

async function updateDistributionChart() {
    const dist = await apiGet("/api/distribution");

    const ctx = document.getElementById("distChart").getContext("2d");

    if (distChart) distChart.destroy();

    distChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: Object.keys(dist),
            datasets: [{
                label: "Count",
                data: Object.values(dist),
                backgroundColor: [
                    "rgba(239,68,68,0.5)",
                    "rgba(234,179,8,0.5)",
                    "rgba(59,130,246,0.5)",
                    "rgba(168,85,247,0.5)",
                    "rgba(16,185,129,0.5)",
                    "rgba(244,63,94,0.5)"
                ],
                borderColor: [
                    "rgb(239,68,68)",
                    "rgb(234,179,8)",
                    "rgb(59,130,246)",
                    "rgb(168,85,247)",
                    "rgb(16,185,129)",
                    "rgb(244,63,94)"
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}