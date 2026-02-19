(function ($) {
    'use strict';
    $(function () {
        const orderSelect = $('#id_order');
        if (!orderSelect.length) return;

        function updateOrderInfo(orderId) {
            if (!orderId) {
                $('.field-order_malumot .readonly').text('—');
                $('.field-order_holati_info .readonly').text('—');
                $('.field-jami_summa_info .readonly').text('—');
                $('.field-qoldiq_info .readonly').text('—');
                return;
            }

            // Pathni tekshirib ko'ring, odatda /api/orders/ID/
            $.ajax({
                url: '/api/orders/' + orderId + '/',
                method: 'GET',
                success: function (data) {
                    $('.field-order_malumot .readonly').text('#' + data.order_code + ' — ' + (data.order_type === 'DINE_IN' ? 'Dine in' : 'Takeaway'));
                    $('.field-order_holati_info .readonly').text(data.status);
                    $('.field-jami_summa_info .readonly').text(Number(data.total).toLocaleString() + ' so\'m');
                    $('.field-qoldiq_info .readonly').text(Number(data.due_amount).toLocaleString() + ' so\'m');

                    // Avtomatik summani to'ldirish (ixtiyoriy, lekin foydali)
                    if (!$('#id_amount').val() || $('#id_amount').val() === '0') {
                        $('#id_amount').val(data.due_amount);
                    }
                },
                error: function () {
                    console.error('Order ma\'lumotlarini yuklab bo\'lmadi');
                }
            });
        }

        orderSelect.on('change', function () {
            updateOrderInfo($(this).val());
        });

        // Agar tanlangan bo'lsa (tahrirlashda)
        if (orderSelect.val()) {
            updateOrderInfo(orderSelect.val());
        }
    });
})(django.jQuery);
