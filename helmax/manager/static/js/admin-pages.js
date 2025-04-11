/**
 * Admin Pages Pagination Configuration
 */

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Utility function to format date
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Initialize pagination for admin wallet page
function initAdminWallet() {
    const pagination = new AdminPagination({
        apiEndpoint: '/manager/api/wallet-transactions',
        onDataLoaded: (data) => {
            const tableBody = document.getElementById('transactionsTableBody');
            const mobileView = document.getElementById('mobileCardView');
            const emptyState = document.getElementById('emptyState');

            if (data.items.length === 0) {
                tableBody.innerHTML = '';
                mobileView.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }

            emptyState.classList.add('hidden');
            
            // Update desktop view
            tableBody.innerHTML = data.items.map(transaction => `
                <tr class="hover:bg-[#111111] transition-colors">
                    <td class="px-6 py-4 text-gray-300">${transaction.id}</td>
                    <td class="px-6 py-4 text-gray-300">${transaction.user.username}</td>
                    <td class="px-6 py-4 text-gray-300">${transaction.type}</td>
                    <td class="px-6 py-4 text-gray-300">${formatCurrency(transaction.amount)}</td>
                    <td class="px-6 py-4 text-gray-300">${transaction.status}</td>
                    <td class="px-6 py-4 text-gray-300">${formatDate(transaction.created_at)}</td>
                    <td class="px-6 py-4">
                        <a href="/manager/wallet-transaction/${transaction.id}" class="text-yellow-500 hover:text-yellow-600">View Details</a>
                    </td>
                </tr>
            `).join('');

            // Update mobile view
            mobileView.innerHTML = data.items.map(transaction => `
                <div class="bg-[#111111] rounded-lg p-4 space-y-3">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-sm text-gray-400">Transaction ID</p>
                            <p class="text-gray-200">${transaction.id}</p>
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full ${transaction.status === 'completed' ? 'bg-green-900/50 text-green-300' : 'bg-yellow-900/50 text-yellow-300'}">
                            ${transaction.status}
                        </span>
                    </div>
                    <div class="space-y-2">
                        <div>
                            <p class="text-sm text-gray-400">User</p>
                            <p class="text-gray-200">${transaction.user.username}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Amount</p>
                            <p class="text-gray-200">${formatCurrency(transaction.amount)}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Date</p>
                            <p class="text-gray-200">${formatDate(transaction.created_at)}</p>
                        </div>
                    </div>
                    <a href="/manager/wallet-transaction/${transaction.id}" class="block text-center text-yellow-500 hover:text-yellow-600 mt-3">
                        View Details
                    </a>
                </div>
            `).join('');
        }
    });
    pagination.loadData();
}

// Initialize pagination for admin brand page
function initAdminBrand() {
    const pagination = new AdminPagination({
        apiEndpoint: '/manager/api/brands',
        onDataLoaded: (data) => {
            const tableBody = document.getElementById('brandsTableBody');
            const mobileView = document.getElementById('mobileCardView');
            const emptyState = document.getElementById('emptyState');

            if (data.items.length === 0) {
                tableBody.innerHTML = '';
                mobileView.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }

            emptyState.classList.add('hidden');
            
            // Update desktop view
            tableBody.innerHTML = data.items.map(brand => `
                <tr class="hover:bg-[#111111] transition-colors">
                    <td class="px-6 py-4 text-gray-300">${brand.name}</td>
                    <td class="px-6 py-4 text-gray-300">${brand.description}</td>
                    <td class="px-6 py-4 text-gray-300">${brand.product_count}</td>
                    <td class="px-6 py-4">
                        <div class="flex space-x-2">
                            <button onclick="editBrand(${brand.id})" class="text-yellow-500 hover:text-yellow-600">Edit</button>
                            <button onclick="deleteBrand(${brand.id})" class="text-red-500 hover:text-red-600">Delete</button>
                        </div>
                    </td>
                </tr>
            `).join('');

            // Update mobile view
            mobileView.innerHTML = data.items.map(brand => `
                <div class="bg-[#111111] rounded-lg p-4 space-y-3">
                    <div class="space-y-2">
                        <div>
                            <p class="text-sm text-gray-400">Brand Name</p>
                            <p class="text-gray-200">${brand.name}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Description</p>
                            <p class="text-gray-200">${brand.description}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Products</p>
                            <p class="text-gray-200">${brand.product_count}</p>
                        </div>
                    </div>
                    <div class="flex justify-end space-x-2 pt-2 border-t border-[#222222]">
                        <button onclick="editBrand(${brand.id})" class="text-yellow-500 hover:text-yellow-600">Edit</button>
                        <button onclick="deleteBrand(${brand.id})" class="text-red-500 hover:text-red-600">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    });
    pagination.loadData();
}
// Initialize pagination for admin products page
function initAdminProducts() {
    const pagination = new AdminPagination({
        apiEndpoint: '/manager/api/products',
        onDataLoaded: (data) => {
            const tableBody = document.getElementById('productsTableBody');
            const mobileView = document.getElementById('mobileCardView');
            const emptyState = document.getElementById('emptyState');

            if (data.items.length === 0) {
                tableBody.innerHTML = '';
                mobileView.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }

            emptyState.classList.add('hidden');
            
            // Update desktop view
            tableBody.innerHTML = data.items.map(product => `
                <tr class="hover:bg-[#111111] transition-colors">
                    <td class="px-6 py-4 text-gray-300">${product.name}</td>
                    <td class="px-6 py-4 text-gray-300">${product.category}</td>
                    <td class="px-6 py-4 text-gray-300">${product.brand}</td>
                    <td class="px-6 py-4 text-gray-300">${formatCurrency(product.price)}</td>
                    <td class="px-6 py-4 text-gray-300">${product.stock}</td>
                    <td class="px-6 py-4 text-gray-300">
                        <span class="px-2 py-1 text-xs rounded-full ${product.is_active ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}">
                            ${product.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td class="px-6 py-4">
                        <div class="flex space-x-2">
                            <a href="/manager/edit-product/${product.id}" class="text-yellow-500 hover:text-yellow-600">Edit</a>
                            <a href="/manager/add-variant/${product.id}" class="text-blue-500 hover:text-blue-600">Add Variant</a>
                            <button onclick="toggleProductStatus(${product.id})" class="text-${product.is_active ? 'red' : 'green'}-500 hover:text-${product.is_active ? 'red' : 'green'}-600">
                                ${product.is_active ? 'Block' : 'Unblock'}
                            </button>
                            <button onclick="deleteProduct(${product.id})" class="text-red-500 hover:text-red-600">Delete</button>
                        </div>
                    </td>
                </tr>
            `).join('');

            // Update mobile view
            mobileView.innerHTML = data.items.map(product => `
                <div class="bg-[#111111] rounded-lg p-4 space-y-3">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-sm text-gray-400">Product Name</p>
                            <p class="text-gray-200">${product.name}</p>
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full ${product.is_active ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}">
                            ${product.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                    <div class="space-y-2">
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <p class="text-sm text-gray-400">Brand</p>
                                <p class="text-gray-200">${product.brand}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-400">Category</p>
                                <p class="text-gray-200">${product.category}</p>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <p class="text-sm text-gray-400">Price</p>
                                <p class="text-gray-200">${formatCurrency(product.price)}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-400">Stock</p>
                                <p class="text-gray-200">${product.stock}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-end space-x-2 pt-2 border-t border-[#222222]">
                        <a href="/manager/edit-product/${product.id}" class="text-yellow-500 hover:text-yellow-600">Edit</a>
                        <a href="/manager/add-variant/${product.id}" class="text-blue-500 hover:text-blue-600">Variant</a>
                        <button onclick="toggleProductStatus(${product.id})" class="text-${product.is_active ? 'red' : 'green'}-500 hover:text-${product.is_active ? 'red' : 'green'}-600">
                            ${product.is_active ? 'Block' : 'Unblock'}
                        </button>
                        <button onclick="deleteProduct(${product.id})" class="text-red-500 hover:text-red-600">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    });
    
    // Store pagination instance globally so we can access it from event handlers
    window.productsPagination = pagination;
    
    pagination.loadData();
}


// Initialize pagination for admin category page
function initAdminCategory() {
    const pagination = new AdminPagination({
        apiEndpoint: '/manager/api/categories',
        onDataLoaded: (data) => {
            const tableBody = document.getElementById('categoriesTableBody');
            const mobileView = document.getElementById('mobileCardView');
            const emptyState = document.getElementById('emptyState');

            if (data.items.length === 0) {
                tableBody.innerHTML = '';
                mobileView.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }

            emptyState.classList.add('hidden');
            
            // Update desktop view
            tableBody.innerHTML = data.items.map(category => `
                <tr class="hover:bg-[#111111] transition-colors">
                    <td class="px-6 py-4 text-gray-300">${category.name}</td>
                    <td class="px-6 py-4 text-gray-300">${category.description}</td>
                    <td class="px-6 py-4 text-gray-300">${category.product_count}</td>
                    <td class="px-6 py-4">
                        <div class="flex space-x-2">
                            <button onclick="editCategory(${category.id})" class="text-yellow-500 hover:text-yellow-600">Edit</button>
                            <button onclick="deleteCategory(${category.id})" class="text-red-500 hover:text-red-600">Delete</button>
                        </div>
                    </td>
                </tr>
            `).join('');

            // Update mobile view
            mobileView.innerHTML = data.items.map(category => `
                <div class="bg-[#111111] rounded-lg p-4 space-y-3">
                    <div class="space-y-2">
                        <div>
                            <p class="text-sm text-gray-400">Category Name</p>
                            <p class="text-gray-200">${category.name}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Description</p>
                            <p class="text-gray-200">${category.description}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Products</p>
                            <p class="text-gray-200">${category.product_count}</p>
                        </div>
                    </div>
                    <div class="flex justify-end space-x-2 pt-2 border-t border-[#222222]">
                        <button onclick="editCategory(${category.id})" class="text-yellow-500 hover:text-yellow-600">Edit</button>
                        <button onclick="deleteCategory(${category.id})" class="text-red-500 hover:text-red-600">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    });
    pagination.loadData();
}

// Initialize pagination for customers page
function initCustomers() {
    const pagination = new AdminPagination({
        apiEndpoint: '/manager/api/customers',
        onDataLoaded: (data) => {
            const tableBody = document.getElementById('customersTableBody');
            const mobileView = document.getElementById('mobileCardView');
            const emptyState = document.getElementById('emptyState');

            if (data.items.length === 0) {
                tableBody.innerHTML = '';
                mobileView.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }

            emptyState.classList.add('hidden');
            
            // Update desktop view
            tableBody.innerHTML = data.items.map(customer => `
                <tr class="hover:bg-[#111111] transition-colors">
                    <td class="px-6 py-4 text-gray-300">${customer.username}</td>
                    <td class="px-6 py-4 text-gray-300">${customer.email}</td>
                    <td class="px-6 py-4 text-gray-300">${customer.phone}</td>
                    <td class="px-6 py-4 text-gray-300">${customer.orders_count}</td>
                    <td class="px-6 py-4 text-gray-300">${formatCurrency(customer.total_spent)}</td>
                    <td class="px-6 py-4">
                        <button onclick="toggleCustomerStatus(${customer.id})" 
                                class="px-3 py-1 rounded text-sm ${customer.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}">
                            ${customer.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                    </td>
                </tr>
            `).join('');

            // Update mobile view
            mobileView.innerHTML = data.items.map(customer => `
                <div class="bg-[#111111] rounded-lg p-4 space-y-3">
                    <div class="space-y-2">
                        <div>
                            <p class="text-sm text-gray-400">Username</p>
                            <p class="text-gray-200">${customer.username}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Email</p>
                            <p class="text-gray-200">${customer.email}</p>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <p class="text-sm text-gray-400">Orders</p>
                                <p class="text-gray-200">${customer.orders_count}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-400">Total Spent</p>
                                <p class="text-gray-200">${formatCurrency(customer.total_spent)}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-end pt-2 border-t border-[#222222]">
                        <button onclick="toggleCustomerStatus(${customer.id})"
                                class="px-3 py-1 rounded text-sm ${customer.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}">
                            ${customer.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                    </div>
                </div>
            `).join('');
        }
    });
    pagination.loadData();
}

// Initialize pagination for return requests page
function initReturnRequests() {
    const pagination = new AdminPagination({
        apiEndpoint: '/manager/api/return-requests',
        onDataLoaded: (data) => {
            const tableBody = document.getElementById('returnRequestsTableBody');
            const mobileView = document.getElementById('mobileCardView');
            const emptyState = document.getElementById('emptyState');

            if (data.items.length === 0) {
                tableBody.innerHTML = '';
                mobileView.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }

            emptyState.classList.add('hidden');
            
            // Update desktop view
            tableBody.innerHTML = data.items.map(request => `
                <tr class="hover:bg-[#111111] transition-colors">
                    <td class="px-6 py-4 text-gray-300">${request.order.order_id}</td>
                    <td class="px-6 py-4 text-gray-300">${request.order.user.username}</td>
                    <td class="px-6 py-4 text-gray-300">${request.product.name}</td>
                    <td class="px-6 py-4 text-gray-300">${request.reason}</td>
                    <td class="px-6 py-4">
                        <span class="px-3 py-1 rounded-full text-sm
                            ${request.status === 'PENDING' ? 'bg-yellow-500/20 text-yellow-500' :
                              request.status === 'APPROVED' ? 'bg-green-500/20 text-green-500' :
                              'bg-red-500/20 text-red-500'}">
                            ${request.status}
                        </span>
                    </td>
                    <td class="px-6 py-4">
                        ${request.status === 'PENDING' ? `
                            <div class="flex space-x-2">
                                <button onclick="handleReturn('${request.id}', 'approve')" 
                                        class="text-green-500 hover:text-green-600">Approve</button>
                                <button onclick="handleReturn('${request.id}', 'reject')"
                                        class="text-red-500 hover:text-red-600">Reject</button>
                            </div>
                        ` : `
                            <span class="text-gray-400">${request.admin_response}</span>
                        `}
                    </td>
                </tr>
            `).join('');

            // Update mobile view
            mobileView.innerHTML = data.items.map(request => `
                <div class="bg-[#111111] rounded-lg p-4 space-y-3">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-sm text-gray-400">Order ID</p>
                            <p class="text-gray-200">${request.order.order_id}</p>
                        </div>
                        <span class="px-3 py-1 rounded-full text-sm
                            ${request.status === 'PENDING' ? 'bg-yellow-500/20 text-yellow-500' :
                              request.status === 'APPROVED' ? 'bg-green-500/20 text-green-500' :
                              'bg-red-500/20 text-red-500'}">
                            ${request.status}
                        </span>
                    </div>
                    <div class="space-y-2">
                        <div>
                            <p class="text-sm text-gray-400">Customer</p>
                            <p class="text-gray-200">${request.order.user.username}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Product</p>
                            <p class="text-gray-200">${request.product.name}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-400">Reason</p>
                            <p class="text-gray-200">${request.reason}</p>
                        </div>
                        ${request.status !== 'PENDING' ? `
                            <div>
                                <p class="text-sm text-gray-400">Admin Response</p>
                                <p class="text-gray-200">${request.admin_response}</p>
                            </div>
                        ` : ''}
                    </div>
                    ${request.status === 'PENDING' ? `
                        <div class="flex justify-end space-x-2 pt-2 border-t border-[#222222]">
                            <button onclick="handleReturn('${request.id}', 'approve')"
                                    class="text-green-500 hover:text-green-600">Approve</button>
                            <button onclick="handleReturn('${request.id}', 'reject')"
                                    class="text-red-500 hover:text-red-600">Reject</button>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        }
    });
    pagination.loadData();
}

// Initialize pagination for sales report page
function initSalesReport() {
    const pagination = new AdminPagination({
        apiEndpoint: '/manager/api/sales-report',
        onDataLoaded: (data) => {
            const tableBody = document.getElementById('salesTableBody');
            const mobileView = document.getElementById('mobileCardView');
            const emptyState = document.getElementById('emptyState');

            // Update summary statistics
            document.getElementById('totalOrders').textContent = data.summary.total_orders;
            document.getElementById('totalSales').textContent = formatCurrency(data.summary.total_sales);
            document.getElementById('totalDiscounts').textContent = formatCurrency(data.summary.total_discounts);

            if (data.items.length === 0) {
                tableBody.innerHTML = '';
                mobileView.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }

            emptyState.classList.add('hidden');
            
            // Update desktop view
            tableBody.innerHTML = data.items.map(order => `
                <tr class="hover:bg-[#111111] transition-colors">
                    <td class="px-6 py-4 text-gray-300">${order.order_id}</td>
                    <td class="px-6 py-4 text-gray-300">${formatDate(order.created_at)}</td>
                    <td class="px-6 py-4 text-gray-300">${order.user.username}</td>
                    <td class="px-6 py-4 text-gray-300">${order.items_count}</td>
                    <td class="px-6 py-4 text-gray-300">${formatCurrency(order.subtotal)}</td>
                    <td class="px-6 py-4 text-gray-300">${formatCurrency(order.discount)}</td>
                    <td class="px-6 py-4 text-gray-300">${formatCurrency(order.total)}</td>
                    <td class="px-6 py-4">
                        <span class="px-3 py-1 rounded-full text-sm
                            ${order.status === 'PROCESSING' ? 'bg-yellow-500/20 text-yellow-500' :
                              order.status === 'SHIPPED' ? 'bg-blue-500/20 text-blue-500' :
                              order.status === 'DELIVERED' ? 'bg-green-500/20 text-green-500' :
                              order.status === 'CANCELLED' ? 'bg-red-500/20 text-red-500' :
                              'bg-gray-500/20 text-gray-500'}">
                            ${order.status}
                        </span>
                    </td>
                </tr>
            `).join('');

            // Update mobile view
            mobileView.innerHTML = data.items.map(order => `
                <div class="bg-[#111111] rounded-lg p-4 space-y-3">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-sm text-gray-400">Order ID</p>
                            <p class="text-gray-200">${order.order_id}</p>
                        </div>
                        <span class="px-3 py-1 rounded-full text-sm
                            ${order.status === 'PROCESSING' ? 'bg-yellow-500/20 text-yellow-500' :
                              order.status === 'SHIPPED' ? 'bg-blue-500/20 text-blue-500' :
                              order.status === 'DELIVERED' ? 'bg-green-500/20 text-green-500' :
                              order.status === 'CANCELLED' ? 'bg-red-500/20 text-red-500' :
                              'bg-gray-500/20 text-gray-500'}">
                            ${order.status}
                        </span>
                    </div>
                    <div class="space-y-2">
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <p class="text-sm text-gray-400">Customer</p>
                                <p class="text-gray-200">${order.user.username}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-400">Date</p>
                                <p class="text-gray-200">${formatDate(order.created_at)}</p>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <p class="text-sm text-gray-400">Items</p>
                                <p class="text-gray-200">${order.items_count}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-400">Subtotal</p>
                                <p class="text-gray-200">${formatCurrency(order.subtotal)}</p>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <p class="text-sm text-gray-400">Discount</p>
                                <p class="text-gray-200">${formatCurrency(order.discount)}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-400">Total</p>
                                <p class="text-gray-200 font-semibold">${formatCurrency(order.total)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    });
    pagination.loadData();
}