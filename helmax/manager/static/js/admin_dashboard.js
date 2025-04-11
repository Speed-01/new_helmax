// Dashboard data handling
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initCharts();
    
    // Initial data fetching
    fetchDashboardMetrics();
    fetchSalesData('monthly'); // Default to monthly view
    fetchTopProducts();
    fetchTopCategories();
    fetchTopBrands();
    
    // Set default dates for ledger
    setDefaultLedgerDates();
    
    // Mobile sidebar toggle
    setupMobileSidebar();
    
    // Add event listener for chart filter
    document.getElementById('chart-filter').addEventListener('change', function(e) {
        fetchSalesData(e.target.value);
    });
});

// Fetch dashboard metrics
function fetchDashboardMetrics() {
    fetch('/manager/api/dashboard-metrics/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update dashboard metrics
            document.getElementById('revenue-value').textContent = formatCurrency(data.total_revenue);
            document.getElementById('orders-value').textContent = data.total_orders;
            document.getElementById('customers-value').textContent = data.new_customers;

            // Update revenue change indicator
            const revenueChange = document.getElementById('revenue-change');
            revenueChange.innerHTML = `
                <i class="fas fa-chart-line mr-1 text-xs"></i>
                <span>Current Period</span>
            `;
            revenueChange.className = 'flex items-center mt-1 text-success';

            // Update orders change indicator
            const ordersChange = document.getElementById('orders-change');
            ordersChange.innerHTML = `
                <i class="fas fa-chart-line mr-1 text-xs"></i>
                <span>Current Period</span>
            `;
            ordersChange.className = 'flex items-center mt-1 text-success';

            // Update customers change indicator
            const customersChange = document.getElementById('customers-change');
            customersChange.innerHTML = `
                <i class="fas fa-chart-line mr-1 text-xs"></i>
                <span>Current Period</span>
            `;
            customersChange.className = 'flex items-center mt-1 text-success';
        })
        .catch(error => {
            console.error('Error fetching dashboard metrics:', error);
            // Update metrics to show error state
            document.getElementById('revenue-value').textContent = 'Error';
            document.getElementById('orders-value').textContent = 'Error';
            document.getElementById('customers-value').textContent = 'Error';
            
            // Update change indicators to show error state
            const indicators = ['revenue-change', 'orders-change', 'customers-change'];
            indicators.forEach(id => {
                const element = document.getElementById(id);
                element.innerHTML = `
                    <i class="fas fa-exclamation-circle mr-1 text-xs"></i>
                    <span>Failed to load</span>
                `;
                element.className = 'flex items-center mt-1 text-danger';
            });
        });
}

// Fetch sales data for chart
function fetchSalesData(filterType) {
    fetch(`/manager/api/sales-data/?filter=${filterType}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update sales chart with data
            updateSalesChart(data.labels, data.values);
        })
        .catch(error => {
            console.error('Error fetching sales data:', error);
            // Update sales chart to show error state
            if (salesChart) {
                salesChart.data.labels = [];
                salesChart.data.datasets[0].data = [];
                salesChart.update();
        }
    });
}

// Fetch top products
function fetchTopProducts() {
    fetch('/manager/api/top-products/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update top products table
            updateTopProductsTable(data.products);
        })
        .catch(error => {
            console.error('Error fetching top products:', error);
            // Show error state in table
            document.getElementById('topProductsTable').innerHTML = 
                '<tr><td colspan="3" class="text-center py-4 text-danger">Failed to load data</td></tr>';
        });
}

// Fetch top categories
function fetchTopCategories() {
    fetch('/manager/api/top-categories/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update top categories table
            updateTopCategoriesTable(data.categories);
        })
        .catch(error => {
            console.error('Error fetching top categories:', error);
            // Show error state in table
            document.getElementById('topCategoriesTable').innerHTML = 
                '<tr><td colspan="3" class="text-center py-4 text-danger">Failed to load data</td></tr>';
        });
}

// Fetch top brands
function fetchTopBrands() {
    fetch('/manager/api/top-brands/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update top brands chart and table
            updateBrandsChart(data.labels, data.values);
            updateTopBrandsTable(data.brands);
        })
        .catch(error => {
            console.error('Error fetching top brands:', error);
            // Show error state in chart and table
            if (brandsChart) {
                brandsChart.data.labels = [];
                brandsChart.data.datasets[0].data = [];
                brandsChart.update();
            }
            document.getElementById('topBrandsTable').innerHTML = 
                '<tr><td colspan="3" class="text-center py-4 text-danger">Failed to load data</td></tr>';
        });
}

// Update top products table
function updateTopProductsTable(products) {
    const tableBody = document.getElementById('topProductsTable');
    tableBody.innerHTML = '';
    
    if (!products || products.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3" class="text-center py-4">No product data available</td></tr>';
        return;
    }
    
    products.forEach(product => {
        if (!product.name) return; // Skip products with no name
        
        const row = document.createElement('tr');
        row.className = 'border-b border-dark-border hover:bg-dark-hover';
        
        row.innerHTML = `
            <td class="px-4 py-3 font-medium">${product.name || 'Unknown Product'}</td>
            <td class="px-4 py-3 text-right">${(product.units_sold || 0).toLocaleString()}</td>
            <td class="px-4 py-3 text-right">${formatCurrency(product.revenue || 0)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Update top categories table
function updateTopCategoriesTable(categories) {
    const tableBody = document.getElementById('topCategoriesTable');
    tableBody.innerHTML = '';
    
    if (!categories || categories.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3" class="text-center py-4">No category data available</td></tr>';
        return;
    }
    
    categories.forEach(category => {
        if (!category.name) return; // Skip categories with no name
        
        const row = document.createElement('tr');
        row.className = 'border-b border-dark-border hover:bg-dark-hover';
        
        row.innerHTML = `
            <td class="px-4 py-3 font-medium">${category.name}</td>
            <td class="px-4 py-3 text-right">${(category.units_sold || 0).toLocaleString()}</td>
            <td class="px-4 py-3 text-right">${formatCurrency(category.revenue || 0)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Update top brands table
function updateTopBrandsTable(brands) {
    const tableBody = document.getElementById('topBrandsTable');
    tableBody.innerHTML = '';
    
    if (!brands || brands.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3" class="text-center py-4">No brand data available</td></tr>';
        return;
    }
    
    brands.forEach(brand => {
        if (!brand.name) return; // Skip brands with no name
        
        const row = document.createElement('tr');
        row.className = 'border-b border-dark-border hover:bg-dark-hover';
        
        row.innerHTML = `
            <td class="px-4 py-3 font-medium">${brand.name}</td>
            <td class="px-4 py-3 text-right">${(brand.units_sold || 0).toLocaleString()}</td>
            <td class="px-4 py-3 text-right">${formatCurrency(brand.revenue || 0)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Update sales chart with new data
function updateSalesChart(labels, values) {
    if (salesChart) {
        salesChart.data.labels = labels || [];
        salesChart.data.datasets[0].data = values || [];
        salesChart.update();
    }
}

// Update brands chart with new data
function updateBrandsChart(labels, values) {
    if (brandsChart) {
        brandsChart.data.labels = labels || [];
        brandsChart.data.datasets[0].data = values || [];
        brandsChart.update();
    }
}

// Format currency helper function
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0
    }).format(value);
}

// Set default dates for ledger
function setDefaultLedgerDates() {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    
    document.getElementById('ledger-start-date').valueAsDate = firstDay;
    document.getElementById('ledger-end-date').valueAsDate = today;
}

// Setup mobile sidebar
function setupMobileSidebar() {
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.getElementById('main-content');
            
            if (sidebar.classList.contains('-translate-x-full')) {
                sidebar.classList.remove('-translate-x-full');
                mainContent.classList.remove('ml-0');
                mainContent.classList.add('ml-64');
            } else {
                sidebar.classList.add('-translate-x-full');
                mainContent.classList.remove('ml-64');
                mainContent.classList.add('ml-0');
            }
        });
    }

    // Handle responsive sidebar on page load
    function handleResponsiveSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('main-content');
        
        if (window.innerWidth < 768) {
            sidebar.classList.add('-translate-x-full');
            mainContent.classList.remove('ml-64');
            mainContent.classList.add('ml-0');
        } else {
            sidebar.classList.remove('-translate-x-full');
            mainContent.classList.remove('ml-0');
            mainContent.classList.add('ml-64');
        }
    }

    // Call on page load
    handleResponsiveSidebar();
    
    // Call on window resize
    window.addEventListener('resize', handleResponsiveSidebar);
}

// Helper function to convert hex to rgba for charts
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Initialize charts - this function should be defined in your HTML or included script
// but is referenced here to ensure it's called properly
function initCharts() {
    // This function should be defined in your HTML
    if (typeof window.initSalesChart === 'function') {
        window.initSalesChart();
    }
    if (typeof window.initBrandsChart === 'function') {
        window.initBrandsChart();
    }
}