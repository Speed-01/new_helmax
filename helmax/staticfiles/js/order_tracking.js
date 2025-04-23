function initOrderTracking(orderId) {
    // Poll for order status updates every second
    const pollInterval = 1000;
    
    let lastTimestamp = 0;

    function updateTimeline() {
        fetch(`/orders/${orderId}/track/status/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Always update the UI to ensure real-time changes are reflected
                    lastTimestamp = data.timestamp;
                    // Update timeline container
                    const timelineContainer = document.getElementById('order-timeline');
                    if (timelineContainer) {
                        timelineContainer.innerHTML = '';
                        
                        data.timeline.forEach(event => {
                            const eventElement = document.createElement('div');
                            eventElement.className = 'timeline-event border-l-2 border-blue-500 pl-4 pb-4';
                            
                            const statusElement = document.createElement('div');
                            statusElement.className = 'status font-semibold text-lg';
                            statusElement.textContent = event.status;
                            
                            const dateElement = document.createElement('div');
                            dateElement.className = 'date text-sm text-gray-600';
                            dateElement.textContent = event.date;
                            
                            const descElement = document.createElement('div');
                            descElement.className = 'description text-gray-700 mt-1';
                            descElement.textContent = event.description;
                            
                            eventElement.appendChild(statusElement);
                            eventElement.appendChild(dateElement);
                            eventElement.appendChild(descElement);
                            
                            timelineContainer.appendChild(eventElement);
                        });
                    }
                    
                    // Update order status
                    const statusElement = document.getElementById('order-status');
                    if (statusElement) {
                        statusElement.textContent = data.order_status;
                    }
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