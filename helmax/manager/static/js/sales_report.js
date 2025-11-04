document.addEventListener('DOMContentLoaded', function() {
    const reportType = document.getElementById('reportType');
    const customDateRange = document.getElementById('customDateRange');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    // Initialize date range visibility based on selected report type
    if (reportType.value === 'custom') {
        customDateRange.classList.remove('hidden');
    } else {
        customDateRange.classList.add('hidden');
    }
    
    // Handle report type change
    reportType.addEventListener('change', function() {
        if (this.value === 'custom') {
            customDateRange.classList.remove('hidden');
        } else {
            customDateRange.classList.add('hidden');
        }
    });
    
    // Date validation - End date can't be before start date
    startDateInput.addEventListener('change', function() {
        // Set minimum end date to be the selected start date
        endDateInput.min = this.value;
        
        // If end date is before start date, update end date to match start date
        if (endDateInput.value && endDateInput.value < this.value) {
            endDateInput.value = this.value;
        }
    });
    
    // Initialize min date for end date if start date is already set
    if (startDateInput.value) {
        endDateInput.min = startDateInput.value;
    }
    
    // Form submission
    document.getElementById('reportForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate dates for custom range
        if (reportType.value === 'custom') {
            if (!startDateInput.value) {
                alert('Please select a start date');
                return;
            }
            if (!endDateInput.value) {
                alert('Please select an end date');
                return;
            }
        }
        
        const formData = new FormData(this);
        const queryParams = new URLSearchParams(formData);
        window.location.href = `?${queryParams.toString()}`;
    });
    
    // Download report function
    window.downloadReport = function(format) {
        const form = document.getElementById('reportForm');
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        params.append('download', format);
        window.location.href = `?${params.toString()}`;
    }
});
