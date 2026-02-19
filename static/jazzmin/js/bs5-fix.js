/**
 * Jazzmin + Bootstrap 5 to'liq moslik tuzatmasi
 * Muammo: Jazzmin 3.x BS4 data-toggle ishlatadi, BS5 esa data-bs-toggle talab qiladi.
 * Yechim: barcha BS4 atributlarni BS5 ga o'girish + dropdown va logout ni to'g'rilash.
 */
(function () {
    'use strict';

    /* ---------- 1. BS4 → BS5 atributlarni almashtirish ---------- */
    function fixBS4Attributes() {
        var map = {
            'data-toggle':  'data-bs-toggle',
            'data-dismiss': 'data-bs-dismiss',
            'data-target':  'data-bs-target',
            'data-parent':  'data-bs-parent',
            'data-ride':    'data-bs-ride',
            'data-slide':   'data-bs-slide',
            'data-slide-to':'data-bs-slide-to',
            'data-offset':  'data-bs-offset',
        };
        Object.keys(map).forEach(function(old) {
            document.querySelectorAll('[' + old + ']').forEach(function(el) {
                el.setAttribute(map[old], el.getAttribute(old));
                // eskisini ham qoldiramiz (AdminLTE uchun)
            });
        });
    }

    /* ---------- 2. Barcha dropdown larni BS5 bilan qayta ishga tushirish ---------- */
    function initDropdowns() {
        if (typeof bootstrap === 'undefined' || !bootstrap.Dropdown) return;
        document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(function(el) {
            // allaqachon inicializatsiya bo'lmagan bo'lsa
            if (!bootstrap.Dropdown.getInstance(el)) {
                new bootstrap.Dropdown(el);
            }
        });
    }

    /* ---------- 3. User menu dropdown — alohida ishlov ---------- */
    function fixUserMenu() {
        // Jazzmin user menu tugmasi
        var userBtn = document.querySelector('.nav-link.btn[data-bs-toggle="dropdown"], #jazzy-usermenu-toggle');
        var userMenu = document.getElementById('jazzy-usermenu');

        if (!userBtn || !userMenu) {
            // ID bo'lmagan holat uchun — barcha nav-item dropdown larni tekshir
            document.querySelectorAll('.nav-item.dropdown').forEach(function(item) {
                var toggle = item.querySelector('[data-bs-toggle="dropdown"]');
                var menu   = item.querySelector('.dropdown-menu');
                if (!toggle || !menu) return;

                toggle.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var isOpen = menu.classList.contains('show');
                    // barcha ochiq menularni yop
                    document.querySelectorAll('.dropdown-menu.show').forEach(function(m) {
                        m.classList.remove('show');
                    });
                    if (!isOpen) {
                        menu.classList.add('show');
                        // joylashuvini to'g'irla
                        var rect = toggle.getBoundingClientRect();
                        menu.style.position = 'fixed';
                        menu.style.top  = (rect.bottom + 2) + 'px';
                        menu.style.left = 'auto';
                        menu.style.right = (window.innerWidth - rect.right) + 'px';
                        menu.style.zIndex = '9999';
                    }
                });
            });

            // Tashqariga bosish — yop
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.nav-item.dropdown')) {
                    document.querySelectorAll('.dropdown-menu.show').forEach(function(m) {
                        m.classList.remove('show');
                    });
                }
            });
        }
    }

    /* ---------- 4. Logout tugmasini to'g'irlash ---------- */
    function fixLogout() {
        // #logout-form mavjud bo'lsa (Jazzmin standart) — hech narsa qilmaylik
        // Agar yo'q bo'lsa, usermenu ichidagi logout havolasini POST formaga o'giramiz
        var logoutLinks = document.querySelectorAll('a[href*="/admin/logout/"]');
        logoutLinks.forEach(function(link) {
            // Forma ichida emasligini tekshir
            if (link.closest('form')) return;
            link.addEventListener('click', function(e) {
                e.preventDefault();
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = link.href;
                var csrf = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrf) {
                    form.appendChild(csrf.cloneNode());
                } else {
                    // Cookie dan CSRF token olish
                    var token = getCookie('csrftoken');
                    if (token) {
                        var input = document.createElement('input');
                        input.type  = 'hidden';
                        input.name  = 'csrfmiddlewaretoken';
                        input.value = token;
                        form.appendChild(input);
                    }
                }
                document.body.appendChild(form);
                form.submit();
            });
        });
    }

    /* ---------- 5. Cookie o'qish yordamchi funksiyasi ---------- */
    function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    /* ---------- 6. AdminLTE pushmenu (sidebar toggle) ---------- */
    function fixPushMenu() {
        var pushBtn = document.querySelector('[data-widget="pushmenu"]');
        if (!pushBtn) return;
        pushBtn.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sidebar-collapse');
            document.body.classList.toggle('sidebar-open');
        });
    }

    /* ---------- Ishga tushirish ---------- */
    document.addEventListener('DOMContentLoaded', function () {
        fixBS4Attributes();
        initDropdowns();
        fixUserMenu();
        fixLogout();
        fixPushMenu();
    });

})();
