function debounce(func, inputs, timeout = 500) {
    for (const input of inputs) {
        let timer;
        const eventType = input.tagName === 'SELECT' ? 'change' : 'keyup';
        input.addEventListener(eventType, () => {
            clearTimeout(timer);
            timer = setTimeout(() => func(), timeout);
        });
    }
}