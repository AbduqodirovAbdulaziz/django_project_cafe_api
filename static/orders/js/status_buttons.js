document.addEventListener('DOMContentLoaded', function () {
    const select = document.querySelector('select[name="new_status"]');
    if (!select) return;

    const container = select.parentElement;
    const options = Array.from(select.options).filter(opt => opt.value !== "");

    if (options.length === 0) {
        // No transitions allowed, maybe show a message
        const badge = document.getElementById('id_holati_badge');
        if (badge) {
            const msg = document.createElement('div');
            msg.style.marginTop = '10px';
            msg.style.color = '#721c24';
            msg.style.fontSize = '0.85rem';
            msg.innerHTML = '<i>Ushbu holatdan boshqa holatga o\'tib bo\'lmaydi.</i>';
            container.appendChild(msg);
        }
        return;
    }

    // Hide original select
    select.style.display = 'none';

    // Create buttons container
    const btnGroup = document.createElement('div');
    btnGroup.className = 'status-btn-group d-flex flex-wrap gap-2 mt-2';

    const colors = {
        'NEW': 'btn-outline-primary',
        'COOKING': 'btn-outline-warning',
        'READY': 'btn-outline-success',
        'SERVED': 'btn-outline-info',
        'CANCELED': 'btn-outline-danger',
        'PAID': 'btn-outline-secondary'
    };

    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.type = 'button';
        const colorClass = colors[opt.value] || 'btn-outline-secondary';
        btn.className = `btn ${colorClass} btn-sm status-change-btn`;
        btn.innerHTML = opt.text;
        btn.setAttribute('data-value', opt.value);

        btn.addEventListener('click', function () {
            if (confirm(`Haqiqatan ham holatni "${opt.text}" ga o'zgartirmoqchimisiz?`)) {
                select.value = opt.value;
                // Find all save buttons and click the "Save and continue editing" one
                // Jazzmin/AdminLTE usually has save buttons at the bottom
                const saveBtn = document.querySelector('input[name="_continue"]');
                if (saveBtn) {
                    saveBtn.click();
                } else {
                    const saveAndAdd = document.querySelector('input[name="_save"]');
                    if (saveAndAdd) saveAndAdd.click();
                }
            }
        });
        btnGroup.appendChild(btn);
    });

    container.appendChild(btnGroup);
});
