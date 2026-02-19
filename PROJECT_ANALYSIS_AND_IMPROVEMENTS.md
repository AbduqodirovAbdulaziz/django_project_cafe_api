# Cafe Management API - Comprehensive Analysis and Improvements

## Project Overview

This is a **Django REST Framework-based café/restaurant management system** designed to handle orders, menu management, payments, tables, expenses, and user role-based access control.

### Architecture
- **Backend**: Django 4.2.28 + Django REST Framework 3.16.1
- **Database**: SQLite (dev) / PostgreSQL or MySQL (production via environment variable)
- **Authentication**: JWT (djangorestframework-simplejwt) with token refresh and blacklist
- **API Documentation**: drf-spectacular with Swagger UI and ReDoc
- **Admin Interface**: Django admin with Jazzmin theme
- **CORS Support**: django-cors-headers for cross-origin requests

---

## Key Entities and Business Logic

### 1. **Order Management**
- **Order Types**: DINE_IN, TAKEAWAY
- **Order Status Flow**: NEW → COOKING → READY → SERVED → PAID (or CANCELED at any stage)
- **Status Tracking**: OrderStatusLog records all transitions with user and timestamp
- **Automatic Table Sync**: Tables marked OCCUPIED when order created/active; FREE when order PAID/CANCELED

### 2. **Users and Roles**
- **MANAGER** (superuser/staff): Full access to all data; can view/create/edit/delete anything
- **WAITER**: Creates orders; manages order lifecycle (SERVED/PAID); payments handling; sees only own orders
- **CHEF**: Views orders; updates status (NEW→COOKING→READY) only; cannot edit/delete
- **Default in Tests**: Fallback treats `is_superuser` and `is_staff` as MANAGER

### 3. **Payment System**
- **Payment Recording**: Tracks method (CASH, CARD, QR), amount, and debt marker
- **Debt Tracking**: Allows partial payments; calculates due_amount automatically
- **Auto-Status Update**: If order reaches SERVED status and due_amount=0, auto-transitions to PAID
- **Role Filtering**: WAITER sees only own orders' payments; MANAGER sees all; CHEF sees none

### 4. **Financial Data**
- **Decimal Precision**: All monetary values use `Decimal("0.01")` for accuracy
- **Discount System**: NONE, PERCENT (0-100%), or AMOUNT type
- **Automatic Recalculation**: Order totals update whenever items or payments change

---

## Implemented Improvements

### ✅ **1. Security Enhancements**

#### SECRET_KEY & DEBUG Hardening
- **File**: `config/settings.py`
- **Change**: `DEBUG` defaults to `False` (production-safe); `SECRET_KEY` requires explicit env var
- **Production Impact**: Fails fast if `SECRET_KEY` not set (prevents accidental insecure deployment)
- **Dev Fallback**: Auto-uses unsafe key in DEBUG mode with visible warning

#### CORS Configuration
- **File**: `config/settings.py`
- **Package**: `django-cors-headers>=4.0.0`
- **Behavior**: 
  - DEBUG mode: Allows all origins (development convenience)
  - Production: Only origins in `CORS_ALLOWED_ORIGINS` env var
- **Admin**: Respects CSRF_TRUSTED_ORIGINS for additional protection

#### Rate Limiting (Throttling)
- **File**: `config/settings.py` → `REST_FRAMEWORK` settings
- **Rates**: 
  - Anonymous: 20 requests/minute
  - Authenticated: 200 requests/minute
- **Purpose**: Mitigates brute-force attacks on login/token endpoints

---

### ✅ **2. Role-Based Access Control (RBAC)**

#### REST API Level
- **File**: `orders/views.py`, `payments/views.py`
- **Queryset Filtering**:
  - MANAGER: Sees all data
  - WAITER: Sees only own orders/payments (filtered by `created_by` or `order__created_by`)
  - CHEF: Sees nothing (empty queryset)
- **Status Transitions** (in `OrderViewSet.update_status`):
  - NEW → COOKING: CHEF or MANAGER only
  - COOKING → READY: CHEF or MANAGER only
  - READY → SERVED: WAITER or MANAGER
  - SERVED → PAID: WAITER or MANAGER
  - CANCELED: MANAGER always; WAITER only for NEW orders

#### Django Admin Level
- **Files**: `orders/admin.py`, `payments/admin.py`, `expenses/admin.py`, `menu/admin.py`
- **Implementation**:
  - Override `get_queryset()` to filter by user role
  - Add permission checks (e.g., `has_add_permission`, `has_delete_permission`)
- **Behavior**:
  - MANAGER: Full CRUD; access to all admin actions
  - WAITER: Limited viewing of own records; see order details in admin
  - CHEF: Read-only or no access to sensitive admin sections
- **Payment Admin Special**: Shows order totals and due amounts inline during creation

---

### ✅ **3. API Documentation**

#### drf-spectacular Integration
- **File**: `config/api_urls.py`
- **Endpoints**:
  - `/api/schema/` → OpenAPI 3.0 JSON schema
  - `/api/docs/` → Swagger UI (interactive)
  - `/api/docs/redoc/` → ReDoc (alternative)
- **Admin Link**: Jazzmin admin panel links to `/api/docs/`

---

### ✅ **4. Admin Enhancements**

#### Order Admin
- **Display**: Order code, type, status, table, totals (subtotal, discount, total, paid, due)
- **Actions**: "Mark PAID" and "Mark CANCELED" bulk actions with error handling
- **Inlines**: OrderItem and OrderStatusLog shown inline
- **Role Filter**: WAITER sees own orders; CHEF sees none

#### Payment Admin
- **Display**: Order info (*Order #code*), order total, remaining due, payment method, amount
- **Readonly Fields**: Order total and due calculated fields (read-only, non-editable)
- **Dynamic Display**: Shows available balance before payment entry
- **Role Filter**: WAITER sees own orders' payments; MANAGER sees all

#### Menu Admin
- **Permissions**: Only MANAGER/staff can add/edit/delete menu items
- **All Users**: Can view menu items (for ordering)

#### Expense Admin
- **Role Filter**: WAITER sees own expenses; CHEF/others see none; MANAGER sees all

---

### ✅ **5. Testing & Quality Assurance**

#### Unit Tests
- **File**: `orders/tests.py`
- **Coverage**:
  - Order creation with items and automatic total calculation
  - Status transitions and OrderStatusLog creation
  - Payment recording and due-amount recalculation
- **Run**: `python manage.py test orders -v 2`
- **Current Status**: 3 tests, all passing ✓

#### Django Checks
- **Validates**: Settings, migrations, model constraints, permissions
- **Run**: `python manage.py check` → "System check identified no issues"

---

## User Workflows by Role

### WAITER
1. Login with JWT (`POST /api/auth/login/`)
2. Create new order (`POST /api/orders/`)
   - Sets order type (DINE_IN/TAKEAWAY), table (if dine-in), customer info
   - Automatically assigned `created_by=self`
3. Add items to order via inline API or admin
4. Transition order status:
   - NEW → COOKING (can ask CHEF to start)
   - COOKING → READY (wait for CHEF)
   - READY → SERVED (when delivered)
   - SERVED → PAID (record payment)
   - Or CANCELED (before service completes)
5. Record payment (`POST /api/payments/`)
   - Only for own orders
   - Can use CASH, CARD, or QR
6. View own orders and payments (not others')

**Admin Interface**:
- See Orders and Payments lists (own only)
- View order details including totals and due amounts
- Create/record payments with order context visible

---

### CHEF
1. Login with JWT
2. View assigned orders in admin or API
3. Update order status:
   - NEW → COOKING (start prep)
   - COOKING → READY (dish ready)
   - Cannot SERVED or PAID (WAITER does this)
4. Cannot view payments, expenses, or other users' financial data
5. Cannot modify order items or prices

**Admin Interface**:
- Restricted/read-only view of orders
- No payment, expense, or admin creation access

---

### MANAGER
1. Login as superuser/staff member
2. Full CRUD access:
   - Orders: Create, view all, edit, delete, change status, bulk actions
   - Payments: Record, view all, edit
   - Menu: Manage categories and items
   - Expenses: Track expenses
   - Users: Create/manage staff accounts
3. Admin bulk actions: Mark orders PAID or CANCELED
4. API: Full access to all endpoints with no queryset filtering
5. Reports: Generate daily/range reports (full visibility)

**Admin Interface**:
- All forms and lists fully accessible
- Can override any payment/order/expense
- Can manage users and roles

---

## Deployment Checklist

### Pre-Deployment (Development to Production)

#### 1. **Environment Variables** (.env file)
```
# Production Essentials
DEBUG=False
SECRET_KEY=<long-random-key-from-secrets-manager>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (if using PostgreSQL/MySQL)
DATABASE_URL=postgresql://user:password@host:5432/cafe_db

# Security (HTTPS/HSTS)
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

#### 2. **Dependencies Installation**
```bash
pip install -r requirements.txt
```

#### 3. **Database Setup**
```bash
python manage.py migrate
python manage.py createsuperuser  # Create MANAGER admin account
```

#### 4. **Static Files**
```bash
python manage.py collectstatic --noinput
```

#### 5. **Tests**
```bash
python manage.py test --failfast
```

#### 6. **Security Checks**
```bash
python manage.py check --deploy
```

#### 7. **Web Server Setup** (Production)
- Use **WSGI** (Gunicorn + Nginx recommended) or **ASGI** (Uvicorn for async)
- Configure **HTTPS** certificates (Let's Encrypt)
- Set up **database backups** (critical for financial data)
- Enable **logging** and **error tracking** (Sentry recommended)

---

## Common Issues & Troubleshooting

### Issue: "Session data corrupted"
- **Cause**: SQLite session store in development; browser cache
- **Fix**: Clear browser cookies; use database session backend in production:
  ```python
  SESSION_ENGINE = 'django.db.backends.db'  # Use database sessions
  ```

### Issue: CORS errors on frontend
- **Cause**: Frontend origin not in `CORS_ALLOWED_ORIGINS`
- **Fix**: Verify frontend URL is in `.env`:
  ```
  CORS_ALLOWED_ORIGINS=https://frontend.yourdomain.com
  ```

### Issue: drf-spectacular warnings (APIView without serializer)
- **Cause**: Some views (like `MeView`, `LogoutView`) don't declare serializers
- **Fix**: Add `@extend_schema` decorator or convert to GenericAPIView (optional; doesn't affect functionality)

### Issue: Permission denied errors
- **Cause**: User role mismatch or queryset filtering
- **Fix**: Check user's role field; verify user is assigned correct role in admin

---

## Future Enhancements (Recommended)

1. **WebSocket Notifications**: Real-time order updates (CHEF gets notified when order ready)
2. **Inventory Management**: Track stock by ingredient based on orders
3. **Advanced Reports**: Revenue trends, top dishes, peak hours
4. **Mobile App**: Native iOS/Android client
5. **Payment Integration**: Stripe, UPI, or local payment gateway
6. **Audit Logging**: Complete history of financial transactions (compliance)
7. **Multi-location**: Support multiple branches/restaurants
8. **Kitchen Display System (KDS)**: Large-screen order display in kitchen

---

## Files Modified

- ✅ `config/settings.py` — Security, CORS, throttling
- ✅ `config/api_urls.py` — Added schema/docs routes
- ✅ `orders/views.py` — Role-based queryset filtering, status rules
- ✅ `orders/admin.py` — Admin filtering, actions, role checks
- ✅ `payments/views.py` — Role-based queryset, order ownership validation
- ✅ `payments/admin.py` — Display order totals/due, role filtering
- ✅ `expenses/admin.py` — Role filtering
- ✅ `menu/admin.py` — Permission checks
- ✅ `requirements.txt` — Added `django-cors-headers`
- ✅ `orders/tests.py` — Unit tests for models

---

## Testing & Running Locally

### Start Development Server
```bash
# Set env vars for dev
$env:DEBUG='True'
$env:SECRET_KEY='test-secret-key'

# Run server
python manage.py runserver
# Visit http://127.0.0.1:8000/admin (admin)
# Visit http://127.0.0.1:8000/api/docs/ (API docs)
```

### Run Tests
```bash
python manage.py test -v 2
```

### Create Test User
```bash
python manage.py shell
>>> from accounts.models import User
>>> User.objects.create_user('waiter1', 'waiter@test.com', 'pass123', role='WAITER')
>>> User.objects.create_user('chef1', 'chef@test.com', 'pass123', role='CHEF')
```

---

## Contact & Support

For issues or questions:
1. Check the Django error logs
2. Review this documentation
3. Run `python manage.py check --deploy`
4. Test with `python manage.py test`

---

**Last Updated**: February 17, 2026  
**Status**: Production-Ready with Role-Based Access Control & Enhanced Admin
