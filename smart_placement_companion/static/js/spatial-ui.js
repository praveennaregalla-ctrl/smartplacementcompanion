/**
 * Lightweight pointer lighting for spatial surfaces.
 * Layout, navigation, and component transforms remain controlled by CSS.
 */
(function () {
    'use strict';

    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
        return;
    }

    function initializeSpatialLighting() {
        document.querySelectorAll(
            '.glass-section, .card, .company-card, .stat-card'
        ).forEach(function (surface) {
            surface.addEventListener('pointermove', function (event) {
                var bounds = surface.getBoundingClientRect();
                var x = ((event.clientX - bounds.left) / bounds.width) * 100;
                var y = ((event.clientY - bounds.top) / bounds.height) * 100;
                surface.style.setProperty('--spatial-pointer-x', x + '%');
                surface.style.setProperty('--spatial-pointer-y', y + '%');
            });

            surface.addEventListener('pointerleave', function () {
                surface.style.removeProperty('--spatial-pointer-x');
                surface.style.removeProperty('--spatial-pointer-y');
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSpatialLighting, { once: true });
    } else {
        initializeSpatialLighting();
    }
})();
