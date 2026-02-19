from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# ENV
# =========================
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="")
DEBUG = env.bool("DEBUG", default=False)

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "unsafe-dev-key-change-me"
    else:
        raise Exception("SECRET_KEY .env faylida ko'rsatilishi shart (production)!")

ALLOWED_HOSTS = [
    h.strip()
    for h in env("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in env("CSRF_TRUSTED_ORIGINS", default="").split(",")
    if o.strip()
]

CORS_ALLOWED_ORIGINS = [
    u.strip()
    for u in env("CORS_ALLOWED_ORIGINS", default="").split(",")
    if u.strip()
]
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# =========================
# APPS
# =========================
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # local apps
    "accounts",
    "menu",
    "tables",
    "orders",
    "payments",
    "expenses",
    "reports",
]

# =========================
# MIDDLEWARE
# =========================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# =========================
# TEMPLATES
# =========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # registration/password_change_*.html override uchun
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# =========================
# DATABASE
# =========================
DATABASE_URL = env("DATABASE_URL", default="").strip()
if DATABASE_URL:
    DATABASES = {"default": env.db()}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =========================
# AUTH
# =========================
AUTH_USER_MODEL = "accounts.User"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =========================
# I18N / TZ
# =========================
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# =========================
# STATIC / MEDIA
# =========================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================
# DRF + JWT + SWAGGER
# =========================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "200/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Cafe API",
    "DESCRIPTION": "Kafe boshqaruv tizimi uchun REST API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# =========================
# SECURITY (faqat prod: DEBUG=False)
# =========================
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "same-origin"


# =========================
# JAZZMIN — Admin panel sozlamalari
# =========================
JAZZMIN_SETTINGS = {
    # ----- Sarlavhalar -----
    "site_title": "Kafe Admin",
    "site_header": "Kafe Boshqaruv Tizimi",
    "site_brand": "☕ Kafe",
    "welcome_sign": "Kafe boshqaruv tizimiga xush kelibsiz",
    "copyright": "Kafe Tizimi © 2026",

    # ----- Qidiruv -----
    "search_model": ["orders.Order", "menu.MenuItem", "accounts.User"],

    # ----- Foydalanuvchi menyusi (o'ng yuqori profil ikonasi) -----
    # Eslatma: Jazzmin standart holda Change password + Log out ni o'zi ko'rsatadi.
    # usermenu_links — qo'shimcha havolalar uchun (standartlarga QO'SHILADI).
    "usermenu_links": [
        {
            "name": "API hujjatlari",
            "url": "/api/docs/",
            "new_window": True,
            "icon": "fas fa-book",
        },
    ],

    # ----- Yuqori menyu (navbar) -----
    "topmenu_links": [
        {
            "name": "🏠 Bosh sahifa",
            "url": "admin:index",
            "permissions": ["auth.view_user"],
        },
        {
            "name": "📋 Buyurtmalar",
            "url": "/admin/orders/order/",
        },
        {
            "name": "📖 API Docs",
            "url": "/api/docs/",
            "new_window": True,
        },
    ],

    # ----- Chap panel menyusi tartibi -----
    "order_with_respect_to": [
        "accounts",
        "orders",
        "menu",
        "tables",
        "payments",
        "expenses",
        "reports",
    ],

    # ----- Ikonalar -----
    "icons": {
        "auth":                       "fas fa-users-cog",
        "auth.user":                  "fas fa-user",
        "auth.Group":                 "fas fa-users",
        "accounts.User":              "fas fa-user-tie",
        "menu.Category":              "fas fa-list",
        "menu.MenuItem":              "fas fa-utensils",
        "tables.Table":               "fas fa-chair",
        "orders.Order":               "fas fa-receipt",
        "orders.OrderItem":           "fas fa-layer-group",
        "orders.OrderStatusLog":      "fas fa-history",
        "payments.Payment":           "fas fa-credit-card",
        "expenses.ExpenseCategory":   "fas fa-tags",
        "expenses.Expense":           "fas fa-money-bill-wave",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # ----- Ko'rinish -----
    "show_ui_builder": False,
    "changeform_format": "single",
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Bootstrap 5 bilan jazzmin 3.x moslik uchun
    "custom_js": "jazzmin/js/bs5-fix.js",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-warning",
    "accent": "accent-warning",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}
