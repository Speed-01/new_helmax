function initOrderDetailsTracking(orderId) {
    // Poll for order status updates every second
    const pollInterval = 1000;
    let lastTimestamp = 0;

    function updateTimeline() {
        fetch(`/orders/${orderId}/track/status/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    lastTimestamp = data.timestamp;
                    
                    // Update vertical progress bar
                    const progressBar = document.querySelector('.bg-[#ff6b00]');
                    if (progressBar) {
                        let progress = 0;
                        if (data.order_status === 'DELIVERED') {
                            progress = 100;
                        } else if (data.order_status === 'SHIPPED') {
                            progress = 66;
                        } else if (data.order_status === 'PROCESSING') {
                            progress = 33;
                        }
                        progressBar.style.height = `${progress}%`;
                    }

                    // Update status points
                    const statusPoints = document.querySelectorAll('.w-4.h-4.rounded-full');
                    const statusTexts = document.querySelectorAll('.text-sm:not(.text-gray-400)');
                    const statusDates = document.querySelectorAll('.text-xs.text-gray-400');
                    
                    const statuses = ['CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED'];
                    const currentStatusIndex = statuses.indexOf(data.order_status);
                    
                    statusPoints.forEach((point, index) => {
                        if (index <= currentStatusIndex) {
                            point.classList.remove('bg-zinc-800');
                            point.classList.add('bg-[#ff6b00]');
                            statusTexts[index].classList.remove('text-zinc-500');
                            statusTexts[index].classList.add('text-white');
                        } else {
                            point.classList.remove('bg-[#ff6b00]');
                            point.classList.add('bg-zinc-800');
                            statusTexts[index].classList.remove('text-white');
                            statusTexts[index].classList.add('text-zinc-500');
                        }
                    });

                    // Update dates
                    if (data.processed_at) {
                        statusDates[1].textContent = new Date(data.processed_at).toLocaleString();
                    }
                    if (data.shipped_at) {
                        statusDates[2].textContent = new Date(data.shipped_at).toLocaleString();
                    }
                    if (data.delivered_at) {
                        statusDates[3].textContent = new Date(data.delivered_at).toLocaleString();
                    }

                    // Update progress bar
                    const progressBar = document.querySelector('.bg-[#ff6b00]');
                    if (progressBar) {
                        let progress = 0;
                        if (data.order_status === 'DELIVERED') {
                            progress = 100;
                        } else if (data.order_status === 'SHIPPED') {
                            progress = 66;
                        } else if (data.order_status === 'PROCESSING') {
                            progress = 33;
                        }
                        progressBar.style.width = `${progress}%`;
                    }

                    // Update status icons
                    const statusSteps = {
                        'CONFIRMED': 1,
                        'PROCESSING': 2,
                        'SHIPPED': 3,
                        'DELIVERED': 4
                    };

                    const currentStep = statusSteps[data.order_status] || 0;
                    document.querySelectorAll('.status-step').forEach((step, index) => {
                        if (index < currentStep) {
                            step.classList.remove('bg-zinc-800');
                            step.classList.add('bg-[#ff6b00]');
                        } else {
                            step.classList.remove('bg-[#ff6b00]');
                            step.classList.add('bg-zinc-800');
                        }
                    });
                }
            })
            .catch(error => console.error('Error fetching order status:', error));
    }
    
    // Initial update
    updateTimeline();
    
    // Set up polling
    const pollTimer = setInterval(updateTimeline, pollInterval);
    
    // Clean up on page unload
    window.addEventListener('unload', () => {
        clearInterval(pollTimer);
    });
}