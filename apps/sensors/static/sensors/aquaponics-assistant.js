(() => {
    const root = document.querySelector('[data-assistant]');
    if (!root) return;

    const panel = root.querySelector('[data-assistant-panel]');
    const launcher = root.querySelector('[data-assistant-open]');
    const messages = root.querySelector('[data-assistant-messages]');
    const form = root.querySelector('[data-assistant-form]');
    const input = root.querySelector('[data-assistant-input]');
    const send = root.querySelector('[data-assistant-send]');
    const status = root.querySelector('[data-assistant-status]');
    const history = [];
    let welcomeMessage = root.querySelector('[data-welcome-message]').textContent.trim();

    function openPanel(open) {
        panel.hidden = !open;
        launcher.setAttribute('aria-expanded', String(open));
        if (open) input.focus();
    }

    function addMessage(role, text) {
        const article = document.createElement('article');
        article.className = `aqua-assistant__message aqua-assistant__message--${role}`;
        article.textContent = text;
        messages.append(article);
        messages.scrollTop = messages.scrollHeight;
        return article;
    }

    function clearConversation() {
        history.length = 0;
        messages.replaceChildren();
        addMessage('assistant', welcomeMessage);
        input.value = '';
        input.focus();
    }

    async function loadConfig() {
        try {
            const response = await fetch('/api/assistant/config/');
            if (!response.ok) throw new Error('Assistant configuration is unavailable.');
            const config = await response.json();
            welcomeMessage = config.welcome_message;
            messages.querySelector('[data-welcome-message]').textContent = welcomeMessage;
            status.textContent = config.available ? 'Онлайн' : 'Требуется настройка API';
            status.dataset.available = String(config.available);
            const suggestions = root.querySelector('[data-assistant-suggestions]');
            config.suggested_questions.forEach(question => {
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = question;
                button.addEventListener('click', () => {
                    input.value = question;
                    form.requestSubmit();
                });
                suggestions.append(button);
            });
        } catch {
            status.textContent = 'Временно недоступен';
            status.dataset.available = 'false';
        }
    }

    launcher.addEventListener('click', () => openPanel(panel.hidden));
    root.querySelector('[data-assistant-close]').addEventListener('click', () => openPanel(false));
    root.querySelector('[data-assistant-clear]').addEventListener('click', clearConversation);

    input.addEventListener('keydown', event => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    form.addEventListener('submit', async event => {
        event.preventDefault();
        const message = input.value.trim();
        if (!message || send.disabled) return;

        addMessage('user', message);
        history.push({ role: 'user', content: message });
        input.value = '';
        send.disabled = true;
        status.textContent = 'Печатает…';
        const typing = addMessage('assistant', 'Печатает…');
        typing.classList.add('is-typing');

        try {
            const response = await fetch('/api/assistant/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value,
                },
                body: JSON.stringify({ message, history: history.slice(-12, -1) }),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Не удалось получить ответ.');
            typing.remove();
            addMessage('assistant', result.reply);
            history.push({ role: 'assistant', content: result.reply });
            if (history.length > 12) history.splice(0, history.length - 12);
            status.textContent = 'Онлайн';
        } catch (error) {
            typing.remove();
            addMessage('assistant', error.message || 'AQ Assistant временно недоступен. Попробуйте позже.');
            history.pop();
            status.textContent = 'Временно недоступен';
        } finally {
            send.disabled = false;
            input.focus();
        }
    });

    loadConfig();
})();
