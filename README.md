<div align="center">

# 🛒 Helmax - Django E-commerce Platform

### A fully functional, production-ready e-commerce platform built with Django 5.1

[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

**[Features](#-features) • [Installation](#-installation) • [API Endpoints](#-api-endpoints) • [Contributing](#-contributing)**

</div>

---

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)
- [License](#license)

---

## 🎯 About

**Helmax** is a comprehensive, production-ready e-commerce solution designed for seamless online shopping experiences. Built with Django 5.1 and modern web technologies, it offers a robust platform for managing products, processing orders, and providing customers with an intuitive shopping interface. 

### 🌟 Key Highlights
- 🔐 **Secure Authentication** - OTP verification & social login integration
- 💳 **Payment Integration** - Razorpay gateway with multiple payment modes
- 📊 **Analytics Dashboard** - Real-time sales tracking with Chart.js visualizations
- 🖼️ **Advanced Image Management** - Cropper.js integration for product variants
- 🎁 **Promotional System** - Coupons, offers, referral codes & wallet system
- 📦 **Order Management** - Complete lifecycle from placement to delivery tracking
- 📱 **Responsive Design** - Mobile-first approach with Tailwind CSS

---

## ✨ Features

### 🔐 Authentication & User Management
- ✅ User registration with **email OTP verification**
- ✅ **Google OAuth** social login integration
- ✅ Secure password reset with OTP
- ✅ User profile management with **referral codes**
- ✅ Multi-address management with default selection
- ✅ Session-based authentication with CSRF protection

### 🛍️ Product & Inventory
- ✅ Product CRUD operations with **variants** (color, size)
- ✅ Multiple product images per variant with primary image selection
- ✅ **Cropper.js image cropping** for variant images (add/edit)
- ✅ Category and brand management with hierarchical structure
- ✅ **Advanced stock management** with size-wise inventory
- ✅ Product offers and **category-wide discounts**
- ✅ Dynamic pricing with offer calculations
- ✅ **Low stock alerts** in admin dashboard
- ✅ Soft delete functionality for products

### 🛒 Shopping Experience
- ✅ Intuitive product listing with **filtering and search**
- ✅ Detailed product pages with **image carousel**
- ✅ Shopping cart with **real-time price calculations**
- ✅ **Wishlist** functionality with persistent storage
- ✅ Product reviews and ratings (1-5 stars)
- ✅ **Coupon code system** with validation (min amount, expiry)
- ✅ Multiple payment methods: **COD, Razorpay, Wallet**
- ✅ Guest checkout with email OTP
- ✅ **Homepage carousel banners** with promotional content

### 💳 Payment & Orders
- ✅ **Razorpay payment gateway** with webhook integration
- ✅ **Retry payment functionality** for failed/pending orders
- ✅ **Auto-cancellation** for expired payments (10-minute window)
- ✅ **Wallet system** with credit/debit transactions
- ✅ Order tracking with **status history timeline**
- ✅ **PDF invoice generation** for completed orders
- ✅ Return and refund management (7-day return policy)
- ✅ COD payment verification on delivery
- ✅ Order confirmation emails with tracking details

### 📊 Admin Dashboard
- ✅ **Chart.js powered** sales analytics with interactive visualizations
- ✅ **Date-filtered sales reports** (weekly/monthly/yearly)
- ✅ Order status summary widgets (Pending, Processing, Delivered)
- ✅ Recent orders tracking with quick actions
- ✅ **Low stock product alerts** with inventory indicators
- ✅ Revenue and customer growth metrics
- ✅ Order management with **bulk status updates**
- ✅ Coupon and offer management with usage analytics
- ✅ Customer management with blocking/unblocking
- ✅ **Sales report export** functionality
- Return request handling
- Wallet transaction monitoring

### 🎁 Promotions & Rewards
- Product-specific offers
- Category-wide offers
- Time-bound promotional campaigns
- Referral program with bonus rewards
- Coupon system (percentage/flat discount)
- Wallet cashback on returns

### 📱 User Interface
- **Responsive carousel banners** on homepage
- Mobile-responsive design with Tailwind CSS
- Clean, modern UI with smooth transitions
- Real-time form validations
- Toast notifications for user feedback
- Loading states and error handling

---

## 🛠️ Tech Stack

<table>
<tr>
<td valign="top" width="50%">

### Backend
- ![Django](https://img.shields.io/badge/Django-5.1-092E20?style=flat&logo=django) - Python web framework
- ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white) - Primary database
- ![Cloudinary](https://img.shields.io/badge/Cloudinary-3448C5?style=flat&logo=cloudinary&logoColor=white) - Media storage
- ![Razorpay](https://img.shields.io/badge/Razorpay-0C2451?style=flat) - Payment gateway
- **Django Signals** - Automated stock management
- **Django Allauth** - Social authentication
- **SMTP (Gmail)** - Email services for OTP

</td>
<td valign="top" width="50%">

### Frontend
- ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white) & ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)
- ![TailwindCSS](https://img.shields.io/badge/Tailwind-38B2AC?style=flat&logo=tailwind-css&logoColor=white) - Utility-first CSS
- ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black) - Client-side scripting
- **Alpine.js** - Lightweight JS framework
- **Chart.js** - Dashboard data visualization
- **Cropper.js** - Image cropping functionality
- **Bootstrap 5** - UI components
- **Font Awesome** - Icon library

</td>
</tr>
</table>

---

## 📁 Project Structure

```
helmax/
├── helmax/                      # Project configuration
│   ├── __init__.py
│   ├── settings.py             # Project settings & configurations
│   ├── urls.py                 # Main URL routing
│   ├── wsgi.py                 # WSGI configuration
│   └── asgi.py                 # ASGI configuration
│
├── manager/                     # Admin management app
│   ├── models.py               # Admin models
│   ├── views.py                # Admin views & dashboard
│   ├── api.py                  # Admin API endpoints
│   ├── urls.py                 # Admin URL patterns
│   ├── forms.py                # Admin forms
│   ├── middleware.py           # Custom middleware
│   ├── decorators.py           # Custom decorators
│   ├── pdf_generator.py        # Invoice PDF generation
│   ├── templates/              # Admin templates
│   │   ├── admin_dashboard.html
│   │   ├── adminProducts.html
│   │   ├── addProducts.html
│   │   ├── addVariant.html    # With image cropping
│   │   ├── editVariant.html   # With image cropping
│   │   ├── adminOrders.html
│   │   ├── sales_report.html
│   │   ├── admin_coupons.html
│   │   ├── admin_offers.html
│   │   └── admin_wallet.html
│   └── migrations/
│
├── store/                       # Customer-facing app
│   ├── models.py               # Core models (User, Cart, Order, etc.)
│   ├── views.py                # Store views & functionality
│   ├── urls.py                 # Store URL patterns
│   ├── forms.py                # Customer forms
│   ├── adapters.py             # Social auth adapters
│   ├── context_processors.py  # Template context processors
│   ├── invoice_generator.py   # Customer invoice generation
│   ├── invoice_views.py       # Invoice view handlers
│   ├── delivery_views.py      # Delivery management
│   ├── order_tracking.py      # Order tracking logic
│   ├── utils.py                # Utility functions
│   ├── templates/              # Store templates
│   │   ├── home.html          # Homepage with carousel
│   │   ├── base.html          # Base template
│   │   ├── product_list.html
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── my_orders.html
│   │   ├── order_details.html
│   │   ├── retry_payment.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── otp_verification.html
│   │   └── wallet.html
│   ├── static/                 # Static files
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── migrations/
│
├── media/                       # User-uploaded media
│   ├── product_images/
│   └── invoices/
│
├── static/                      # Collected static files
│   ├── css/
│   ├── js/
│   └── images/
│
├── staticfiles/                 # Production static files
│
├── requirements.txt             # Python dependencies
├── manage.py                    # Django management script
├── .env                         # Environment variables (not in repo)
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/Speed-01/new_helmax.git
cd new_helmax/helmax
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv myworld
myworld\Scripts\activate

# Linux/Mac
python3 -m venv myworld
source myworld/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note**: Ensure PostgreSQL is installed and running on your system before proceeding.

### Step 4: Configure Environment Variables
Create a `.env` file in the project root and add:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Email Configuration (Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Razorpay
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Social Auth (Google OAuth)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret
```

### Step 5: Database Setup
```bash
# Create PostgreSQL database
createdb helmax_db

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 7: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 8: Run Development Server
```bash
python manage.py runserver
```

The application will be available at:
- 🌐 **Customer Store**: `http://127.0.0.1:8000/`
- 🔧 **Admin Panel**: `http://127.0.0.1:8000/manager/`
- ⚙️ **Django Admin**: `http://127.0.0.1:8000/admin/`

---

## 🔑 Environment Variables

The application requires the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | ✅ |
| `DEBUG` | Debug mode (True/False) | ✅ |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | ✅ |
| `DATABASE_NAME` | PostgreSQL database name | ✅ |
| `DATABASE_USER` | PostgreSQL username | ✅ |
| `DATABASE_PASSWORD` | PostgreSQL password | ✅ |
| `EMAIL_HOST_USER` | Gmail email address | ✅ |
| `EMAIL_HOST_PASSWORD` | Gmail app password | ✅ |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | ✅ |
| `CLOUDINARY_API_KEY` | Cloudinary API key | ✅ |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | ✅ |
| `RAZORPAY_KEY_ID` | Razorpay API key ID | ✅ |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret | ✅ |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY` | Google OAuth client ID | ⚠️ |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET` | Google OAuth client secret | ⚠️ |

---

## 💻 Usage

### Admin Panel
Access the admin panel at `http://127.0.0.1:8000/admin/`

**Admin Features:**
- Dashboard with sales analytics
- Product and variant management with image cropping
- Order processing and tracking
- Coupon and offer creation
- Return request handling
- Wallet transaction management
- Sales report generation

### Customer Interface
Access the store at `http://127.0.0.1:8000/`

**Customer Features:**
- Browse products with filters
- Add to cart and wishlist
- Apply coupons at checkout
- Track orders in real-time
- Request returns within 7 days
- Manage wallet balance
- View order invoices

---

## 🔌 API Endpoints

### Admin API
```
GET  /manager/api/dashboard-metrics/     # Dashboard metrics (revenue, orders, users)
GET  /manager/api/sales-data/            # Sales chart data with filtering
GET  /manager/api/orders/                # List all orders
GET  /manager/api/products/              # List all products
POST /manager/api/products/              # Create new product
PUT  /manager/api/products/<id>/         # Update product
DELETE /manager/api/products/<id>/       # Delete product
```

### Store API
```
GET    /store/api/products/              # List products with filters
POST   /store/api/cart/add/              # Add item to cart
POST   /store/api/cart/update/           # Update cart item quantity
DELETE /store/api/cart/remove/           # Remove item from cart
POST   /store/api/checkout/              # Process order checkout
GET    /store/api/orders/<id>/           # Get order details
POST   /store/api/wishlist/toggle/       # Add/remove from wishlist
```

### Payment API
```
POST /store/payment/create-order/        # Create Razorpay order
POST /store/payment/verify/              # Verify payment signature
POST /store/payment/wallet/              # Process wallet payment
```

---

## 🔮 Future Improvements

### 🎯 Planned Features
- [ ] 🤖 **AI Recommendation System** - ML-powered product suggestions
- [ ] 💬 **Live Chat Support** - Real-time customer assistance
- [ ] 📱 **Mobile Application** - React Native/Flutter app
- [ ] 🌍 **Multi-language Support** - Internationalization (i18n)
- [ ] 📊 **AI Analytics Dashboard** - Predictive insights & trends
- [ ] 📦 **Inventory Forecasting** - Smart stock predictions
- [ ] 📧 **Email Marketing** - Automated campaign management
- [ ] 📲 **SMS Notifications** - Order status updates via SMS
- [ ] 🔍 **Product Comparison** - Side-by-side feature comparison
- [ ] 🎯 **Advanced Search** - Filters (price, ratings, availability)
- [ ] 🔄 **Subscription Products** - Recurring order management
- [ ] 🎁 **Gift Card System** - Digital gift cards & vouchers
- [ ] 🔔 **Push Notifications** - Browser push for order updates
- [ ] 🚚 **Multi-warehouse** - Multiple fulfillment centers
- [ ] Loyalty points program
- [ ] Vendor/multi-seller marketplace
- [ ] Progressive Web App (PWA) support

---

## 👥 Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/Speed-01">
        <img src="https://github.com/Speed-01.png" width="100px;" alt="Antony Davis"/>
        <br />
        <sub><b>Antony Davis</b></sub>
      </a>
      <br />
      <sub>Lead Developer</sub>
    </td>
  </tr>
</table>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Speed-01/new_helmax/issues).

### How to Contribute

1. **Fork** the project repository
2. **Create** your feature branch 
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit** your changes 
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push** to the branch 
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open** a Pull Request with detailed description

### Contribution Guidelines
- Follow PEP 8 coding standards
- Write clear commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## 📞 Contact

**Antony Davis**
- GitHub: [@Speed-01](https://github.com/Speed-01)
- Project Link: [https://github.com/Speed-01/new_helmax](https://github.com/Speed-01/new_helmax)

---

## 🙏 Acknowledgments

- [Django Documentation](https://docs.djangoproject.com/) - Comprehensive framework documentation
- [Razorpay API](https://razorpay.com/docs/) - Payment gateway integration
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Cloudinary](https://cloudinary.com/documentation) - Media management platform
- [Chart.js](https://www.chartjs.org/) - Beautiful data visualizations
- [Cropper.js](https://fengyuanchen.github.io/cropperjs/) - Image cropping library
- Stack Overflow Community - Problem-solving support

---

<div align="center">
  <p>Made with ❤️ by Antony Davis</p>
  <p>⭐ Star this repository if you found it helpful!</p>
</div>
