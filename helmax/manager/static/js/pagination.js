/**
 * Pagination Module for Admin Pages
 */
class AdminPagination {
    constructor(options) {
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalItems = 0;
        this.itemsPerPage = 10;
        this.searchQuery = "";
        this.statusFilter = "all";
        this.paymentFilter = "all";
        this.sortField = "created_at";
        this.sortDirection = "desc";

        // DOM Elements
        this.searchInput = document.getElementById('searchInput');
        this.statusFilterSelect = document.getElementById('statusFilter');
        this.paymentFilterSelect = document.getElementById('paymentFilter');
        this.firstPageBtn = document.getElementById('firstPage');
        this.prevPageBtn = document.getElementById('prevPage');
        this.nextPageBtn = document.getElementById('nextPage');
        this.lastPageBtn = document.getElementById('lastPage');
        this.pageSizeSelect = document.getElementById('pageSizeSelect');
        this.paginationNumbers = document.getElementById('paginationNumbers');
        this.itemsFromSpan = document.getElementById('itemsFrom');
        this.itemsToSpan = document.getElementById('itemsTo');
        this.totalItemsSpan = document.getElementById('totalItems');

        // Merge custom options
        Object.assign(this, options);

        // Initialize event listeners
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Search input
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce(() => {
                this.searchQuery = this.searchInput.value;
                this.currentPage = 1;
                this.loadData();
            }, 300));
        }

        // Status filter
        if (this.statusFilterSelect) {
            this.statusFilterSelect.addEventListener('change', () => {
                this.statusFilter = this.statusFilterSelect.value;
                this.currentPage = 1;
                this.loadData();
            });
        }

        // Payment filter
        if (this.paymentFilterSelect) {
            this.paymentFilterSelect.addEventListener('change', () => {
                this.paymentFilter = this.paymentFilterSelect.value;
                this.currentPage = 1;
                this.loadData();
            });
        }

        // Page size selector
        if (this.pageSizeSelect) {
            this.pageSizeSelect.addEventListener('change', () => {
                this.itemsPerPage = parseInt(this.pageSizeSelect.value);
                this.currentPage = 1;
                this.loadData();
            });
        }

        // Navigation buttons
        if (this.firstPageBtn) {
            this.firstPageBtn.addEventListener('click', () => this.goToPage(1));
        }
        if (this.prevPageBtn) {
            this.prevPageBtn.addEventListener('click', () => this.goToPage(this.currentPage - 1));
        }
        if (this.nextPageBtn) {
            this.nextPageBtn.addEventListener('click', () => this.goToPage(this.currentPage + 1));
        }
        if (this.lastPageBtn) {
            this.lastPageBtn.addEventListener('click', () => this.goToPage(this.totalPages));
        }

        // Sort headers
        document.querySelectorAll('[data-sort]').forEach(header => {
            header.addEventListener('click', () => this.handleSort(header.dataset.sort));
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    handleSort(field) {
        if (this.sortField === field) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortField = field;
            this.sortDirection = 'asc';
        }
        this.loadData();
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) return;
        this.currentPage = page;
        this.loadData();
    }

    updatePaginationUI() {
        // Update items count display
        const from = Math.min((this.currentPage - 1) * this.itemsPerPage + 1, this.totalItems);
        const to = Math.min(this.currentPage * this.itemsPerPage, this.totalItems);
        
        if (this.itemsFromSpan) this.itemsFromSpan.textContent = from;
        if (this.itemsToSpan) this.itemsToSpan.textContent = to;
        if (this.totalItemsSpan) this.totalItemsSpan.textContent = this.totalItems;

        // Update navigation buttons state
        if (this.firstPageBtn) this.firstPageBtn.disabled = this.currentPage === 1;
        if (this.prevPageBtn) this.prevPageBtn.disabled = this.currentPage === 1;
        if (this.nextPageBtn) this.nextPageBtn.disabled = this.currentPage === this.totalPages;
        if (this.lastPageBtn) this.lastPageBtn.disabled = this.currentPage === this.totalPages;

        // Generate page numbers
        this.generatePageNumbers();
    }

    generatePageNumbers() {
        if (!this.paginationNumbers) return;

        this.paginationNumbers.innerHTML = '';
        let pages = [];

        // Always show first page
        pages.push(1);

        // Calculate range around current page
        let rangeStart = Math.max(2, this.currentPage - 1);
        let rangeEnd = Math.min(this.totalPages - 1, this.currentPage + 1);

        // Add ellipsis if needed before range
        if (rangeStart > 2) {
            pages.push('...');
        }

        // Add pages in range
        for (let i = rangeStart; i <= rangeEnd; i++) {
            pages.push(i);
        }

        // Add ellipsis if needed after range
        if (rangeEnd < this.totalPages - 1) {
            pages.push('...');
        }

        // Always show last page if there is more than one page
        if (this.totalPages > 1) {
            pages.push(this.totalPages);
        }

        // Create and append page number elements
        pages.forEach(page => {
            if (page === '...') {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'page-ellipsis';
                ellipsis.textContent = '...';
                this.paginationNumbers.appendChild(ellipsis);
            } else {
                const button = document.createElement('button');
                button.className = `page-number ${page === this.currentPage ? 'active' : ''}`;
                button.textContent = page;
                button.addEventListener('click', () => this.goToPage(page));
                this.paginationNumbers.appendChild(button);
            }
        });
    }

    async loadData() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.itemsPerPage,
                search: this.searchQuery,
                status: this.statusFilter,
                payment: this.paymentFilter,
                sort_field: this.sortField,
                sort_direction: this.sortDirection
            });
    
            const response = await fetch(`${this.apiEndpoint}?${params}`);
            
            // Check if the response is ok before trying to parse JSON
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
    
            this.totalItems = data.total;
            this.totalPages = Math.ceil(this.totalItems / this.itemsPerPage);
    
            // Update UI elements
            this.updatePaginationUI();
    
            // Call the provided callback with the data
            if (this.onDataLoaded) {
                this.onDataLoaded(data);
            }
        } catch (error) {
            console.error('Error loading data:', error);
            
            // Call onDataLoaded with null to indicate an error occurred
            if (this.onDataLoaded) {
                this.onDataLoaded(null);
            }
            
            // Show an error message to the user
            const emptyState = document.getElementById('emptyState');
            if (emptyState) {
                const heading = emptyState.querySelector('h3');
                const message = emptyState.querySelector('p');
                
                if (heading) heading.textContent = 'Error loading data';
                if (message) message.textContent = 'There was a problem fetching the data. Please try again later.';
                
                emptyState.classList.remove('hidden');
            }
        }
    }