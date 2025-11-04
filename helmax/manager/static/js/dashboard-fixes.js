// Dashboard fixes for Helmax admin panel
document.addEventListener('DOMContentLoaded', function() {
    // Fix currency format to use INR instead of USD
    const originalFormatCurrency = window.formatCurrency;
    window.formatCurrency = function(value) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0
        }).format(value);
    };
    
    // Fix brand chart scaling
    const originalInitBrandsChart = window.initBrandsChart;
    window.initBrandsChart = function() {
        // Call the original function first
        if (originalInitBrandsChart) {
            originalInitBrandsChart();
        }
        
        // Then modify the chart options
        if (window.brandsChart) {
            // Set a reasonable max value for the y-axis
            window.brandsChart.options.scales.y.suggestedMax = 50000;
            // Update the chart
            window.brandsChart.update();
        }
    };
    
    // Override the fetch functions to filter out default values
    const originalFetchTopProducts = window.fetchTopProducts;
    window.fetchTopProducts = function() {
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
                
                // Filter out any products with default or empty names
                const filteredProducts = data.products.filter(product => 
                    product.name && 
                    product.name !== 'Unknown Product' && 
                    product.name.trim() !== '');
                
                // Update top products table with filtered data
                updateTopProductsTable(filteredProducts);
            })
            .catch(error => {
                console.error('Error fetching top products:', error);
                // Show error state in table
                document.getElementById('topProductsTable').innerHTML = 
                    '<tr><td colspan="3" class="text-center py-4 text-danger">Failed to load data</td></tr>';
            });
    };
    
    // Override the fetch functions to filter out default values
    const originalFetchTopCategories = window.fetchTopCategories;
    window.fetchTopCategories = function() {
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
                
                // Filter out any categories with default or empty names
                const filteredCategories = data.categories.filter(category => 
                    category.name && 
                    category.name !== 'Uncategorized' && 
                    category.name.trim() !== '');
                
                // Update top categories table with filtered data
                updateTopCategoriesTable(filteredCategories);
            })
            .catch(error => {
                console.error('Error fetching top categories:', error);
                // Show error state in table
                document.getElementById('topCategoriesTable').innerHTML = 
                    '<tr><td colspan="3" class="text-center py-4 text-danger">Failed to load data</td></tr>';
            });
    };
    
    // Override the fetch functions to filter out default values
    const originalFetchTopBrands = window.fetchTopBrands;
    window.fetchTopBrands = function() {
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
                
                // Filter out any brands with default or empty names
                const filteredBrands = data.brands.filter(brand => 
                    brand.name && 
                    brand.name !== 'Unbranded' && 
                    brand.name.trim() !== '');
                
                // Filter the labels and values arrays to match
                const filteredLabels = [];
                const filteredValues = [];
                
                filteredBrands.forEach((brand, index) => {
                    if (index < data.labels.length && index < data.values.length) {
                        filteredLabels.push(data.labels[index]);
                        filteredValues.push(data.values[index]);
                    }
                });
                
                // Update top brands chart and table with filtered data
                updateBrandsChart(filteredLabels, filteredValues);
                updateTopBrandsTable(filteredBrands);
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
    };
    
    // Re-initialize charts with our fixes
    if (typeof window.initCharts === 'function') {
        window.initCharts();
    }
    
    // Re-fetch data with our fixed functions
    if (typeof window.fetchTopProducts === 'function') {
        window.fetchTopProducts();
    }
    
    if (typeof window.fetchTopCategories === 'function') {
        window.fetchTopCategories();
    }
    
    if (typeof window.fetchTopBrands === 'function') {
        window.fetchTopBrands();
    }
});
