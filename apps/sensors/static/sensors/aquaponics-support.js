(() => {
    const form = document.querySelector('[data-donation-form]');
    if (!form) return;

    const message = form.querySelector('[data-donation-message]');
    const customOption = form.querySelector('input[value="custom"]');
    const customField = form.querySelector('[data-custom-amount]');
    const customInput = form.querySelector('[data-custom-amount-input]');

    form.querySelectorAll('input[name="amount"]').forEach(input => {
        input.addEventListener('change', () => {
            const isCustom = customOption.checked;
            customField.hidden = !isCustom;
            if (isCustom) customInput.focus();
        });
    });

    form.querySelector('[name="is_anonymous"]').addEventListener('change', event => {
        const disabled = event.currentTarget.checked;
        form.querySelector('[name="donor_name"]').disabled = disabled;
        form.querySelector('[name="donor_email"]').disabled = disabled;
    });

    fetch('/api/donations/statistics/')
        .then(response => {
            if (!response.ok) throw new Error('Не удалось загрузить статистику.');
            return response.json();
        })
        .then(stats => {
            document.querySelector('[data-donation-total]').textContent = Number(stats.total_amount).toLocaleString('ru-RU');
            document.querySelector('[data-donation-count]').textContent = stats.confirmed_donations.toLocaleString('ru-RU');
        })
        .catch(() => {
            document.querySelector('[data-donation-total]').textContent = '—';
            document.querySelector('[data-donation-count]').textContent = '—';
            message.textContent = 'Статистика пожертвований временно недоступна.';
        });
})();
