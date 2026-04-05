function debounce(func, inputs, timeout = 500) {
    for (const input of inputs) {
        let timer;
        input.addEventListener('keyup', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {func()} ,timeout);
        });
    }
}