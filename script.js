// Basic tab functionality
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove active class from all tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        
        // Add active class to clicked tab
        tab.classList.add('active');
        
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
        });
        
        // Show the selected tab content
        const tabName = tab.getAttribute('data-tab');
        if (tabName === 'connected') {
            document.getElementById('connected-sources').style.display = 'block';
        } else if (tabName === 'available') {
            document.getElementById('available-integrations').style.display = 'block';
        }
    });
});

// Modal functionality
const modal = document.getElementById('add-source-modal');
const addSourceBtn = document.getElementById('add-source-btn');
const closeModalBtn = document.getElementById('close-modal');

addSourceBtn.addEventListener('click', () => {
    modal.style.display = 'block';
});

closeModalBtn.addEventListener('click', () => {
    modal.style.display = 'none';
});

// Close modal when clicking outside
window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// Chart Data
document.addEventListener('DOMContentLoaded', function() {
    // Get the chart canvas
    const chartCanvas = document.getElementById('performance-chart');
    
    // Sample data for the past 7 days
    const dates = [];
    const spendData = [];
    const conversionsData = [];
    
    // Generate dates for the last 7 days
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Generate random data
        spendData.push(Math.floor(Math.random() * 1000) + 1500);
        conversionsData.push(Math.floor(Math.random() * 50) + 70);
    }
    
    // Create the chart
    new Chart(chartCanvas, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Daily Spend ($)',
                    data: spendData,
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y'
                },
                {
                    label: 'Conversions',
                    data: conversionsData,
                    borderColor: '#4cc9f0',
                    backgroundColor: 'rgba(76, 201, 240, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Spend ($)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Conversions'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.dataset.label === 'Daily Spend ($)') {
                                label += '$' + context.parsed.y.toFixed(2);
                            } else {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
    
    // Generate recommendations button functionality
    document.getElementById('generate-recommendations').addEventListener('click', function() {
        alert('Analyzing data and generating new recommendations...');
        
        // In a real app, this would trigger the recommendation algorithm
        setTimeout(() => {
            alert('New recommendations generated successfully!');
        }, 2000);
    });
});

// Mock API data handling functions
class AdPlatformAPI {
    constructor(platform) {
        this.platform = platform;
    }
    
    async fetchData(startDate, endDate) {
        // In a real app, this would make API calls to respective platforms
        console.log(`Fetching data from ${this.platform} for period ${startDate} to ${endDate}`);
        
        // Mock data for demonstration
        return {
            spend: Math.random() * 10000,
            impressions: Math.random() * 1000000,
            clicks: Math.random() * 50000,
            conversions: Math.random() * 1000
        };
    }
    
    async applyBudgetChange(campaignId, percentChange) {
        console.log(`Changing budget for ${campaignId} by ${percentChange}%`);
        // In a real app, this would make API calls to update budgets
        return {
            success: true,
            newDailyBudget: 150.00
        };
    }
}

// Budget optimization algorithm (simplified)
class BudgetOptimizer {
    constructor(platformData) {
        this.platformData = platformData;
    }
    
    generateRecommendations() {
        // In a real app, this would contain complex logic based on performance metrics
        const recommendations = [];
        
        // Example recommendation logic (simplified)
        for (const platform in this.platformData) {
            const data = this.platformData[platform];
            
            // Check ROAS - if high, suggest increasing budget
            if (data.roas > 3.0) {
                recommendations.push({
                    type: 'increase',
                    platform: platform,
                    campaign: 'Top Performer',
                    percentage: 20,
                    reason: 'High ROAS of ' + data.roas.toFixed(1) + 'x'
                });
            }
            
            // Check CPA - if high, suggest decreasing budget
            if (data.cpa > 25) {
                recommendations.push({
                    type: 'decrease',
                    platform: platform,
                    campaign: 'Underperformer',
                    percentage: -30,
                    reason: 'High CPA of $' + data.cpa.toFixed(2)
                });
            }
        }
        
        return recommendations;
    }
}

// Example of how the optimization would work (not actually executed in this demo)
function runOptimizationExample() {
    // Create API clients
    const metaAPI = new AdPlatformAPI('Meta Ads');
    const googleAPI = new AdPlatformAPI('Google Ads');
    
    // Fetch data
    Promise.all([
        metaAPI.fetchData('2025-03-28', '2025-04-04'),
        googleAPI.fetchData('2025-03-28', '2025-04-04')
    ]).then(results => {
        // Process data
        const platformData = {
            'Meta Ads': {
                ...results[0],
                cpa: results[0].spend / results[0].conversions,
                roas: (results[0].conversions * 150) / results[0].spend
            },
            'Google Ads': {
                ...results[1],
                cpa: results[1].spend / results[1].conversions,
                roas: (results[1].conversions * 150) / results[1].spend
            }
        };
        
        // Generate recommendations
        const optimizer = new BudgetOptimizer(platformData);
        const recommendations = optimizer.generateRecommendations();
        
        console.log('Generated recommendations:', recommendations);
        
        // Apply changes (would typically be user-initiated)
        // metaAPI.applyBudgetChange('Campaign123', recommendations[0].percentage);
    });
}

// For demonstration only
console.log('Budget optimization tool loaded. See runOptimizationExample() in console to see how the optimization would work.');