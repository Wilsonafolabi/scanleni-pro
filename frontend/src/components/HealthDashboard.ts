import Chart from 'chart.js/auto';

export function renderDashboard(container: HTMLElement, score: number, trends: any) {
  container.innerHTML = `
    <canvas id="scoreChart" class="mb-3"></canvas>
    <div class="d-flex justify-content-between text-muted small">
      <span>Scans: ${trends?.scan_count || 0}</span>
      <span>Trend: ${trends?.trend || 'stable'}</span>
    </div>
  `;

  // ✅ FIX: Cast to HTMLCanvasElement so Chart.js accepts it
  const canvas = container.querySelector('#scoreChart') as HTMLCanvasElement;

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Safe', 'Flagged'],
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: ['#00e599', '#ff4444'],
        borderWidth: 0,
        circumference: 270,
        rotation: 135
      }]
    },
    options: {
      responsive: true,
      cutout: '70%',
      plugins: { 
        legend: { display: false }, 
        tooltip: { enabled: false } 
      }
    }
  });

  // ✅ FIX: Added safe check and type cast for trendInsight
  const insightEl = document.getElementById('trendInsight') as HTMLElement;
  if (insightEl) {
    insightEl.textContent = trends?.insight || 'Scan more to unlock insights.';
  }
}