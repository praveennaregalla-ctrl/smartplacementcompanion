(function () {
    'use strict';

    document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
        var input = document.getElementById(button.getAttribute('data-password-toggle'));
        var icon = button.querySelector('i');

        if (!input || !icon) {
            return;
        }

        button.addEventListener('click', function () {
            var shouldShow = input.type === 'password';
            input.type = shouldShow ? 'text' : 'password';
            button.setAttribute('aria-pressed', String(shouldShow));
            button.setAttribute('aria-label', shouldShow ? 'Hide password' : 'Show password');
            icon.classList.toggle('bi-eye', !shouldShow);
            icon.classList.toggle('bi-eye-slash', shouldShow);
        });
    });

    document.querySelectorAll('[data-auth-form]').forEach(function (form) {
        form.addEventListener('submit', function () {
            var submitButton = form.querySelector('.auth-submit');
            var label = submitButton && submitButton.querySelector('span');

            if (!submitButton || !label) {
                return;
            }

            submitButton.disabled = true;
            submitButton.setAttribute('aria-busy', 'true');
            label.textContent = 'Signing in...';
        });
    });
})();
