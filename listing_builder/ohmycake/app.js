/**
 * location: ohmycake/app.js
 * Purpose: Main JavaScript for Oh My Cake website - form handling, animations, interactions
 * NOT for: Third-party library code, analytics tracking, inline event handlers
 */

'use strict';

// ============================
// CONSTANTS - No magic numbers
// ============================
const CONFIG = {
    NAVBAR_SCROLL_THRESHOLD: 50,          // px - when navbar becomes solid
    VALIDATION_ERROR_TIMEOUT: 5000,       // ms - auto-hide validation errors
    PHONE_REGEX: /^[0-9]{3}[\s-]?[0-9]{3}[\s-]?[0-9]{3}$/,
    PHONE_PREFIX: '+48',
    MIN_PHONE_DIGITS: 9,
    TOTAL_FORM_STEPS: 4,
    INTERSECTION_THRESHOLD: 0.1,
    INTERSECTION_ROOT_MARGIN: '0px 0px -50px 0px',
    COOKIE_BANNER_DELAY: 1000,            // ms - delay before showing cookie banner
};

// ============================
// INPUT SANITIZATION - XSS Prevention
// ============================
function sanitizeInput(str) {
    if (typeof str !== 'string') return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .trim();
}

// Sanitize object values recursively
function sanitizeFormData(data) {
    const sanitized = {};
    for (const [key, value] of Object.entries(data)) {
        sanitized[key] = sanitizeInput(value);
    }
    return sanitized;
}

// ============================
// GLOBAL ERROR BOUNDARY
// ============================
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Global error:', { msg, url, lineNo, columnNo, error });
    // Don't show script errors from external resources to users
    return false;
};

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

// ============================
// Flavor data for configurator
// ============================
const flavors = {
    blacha: [
        'Sernik Tradycyjny',
        'Sernik Papieski',
        'Snickers',
        'Makowiec',
        'Filadelfia',
        'Czekoladowy z Wiśnią',
        'Łącki przekładaniec',
        'Malinowa Chmurka',
        'Kora Orzechowa',
        'Pani Walewska',
        'Sękaczek',
        'Góra Lodowa',
        '3 Bit',
        'Szarlotka Królewska',
        'Marysieńka',
        'Ananasowiec',
        'Leśny Mech',
        'Porzeczkowiec',
        'Gruszka z Bezą',
        'Shrek'
    ],
    tortownica: [
        'Sernik Pistacjowy',
        'Biała Czekolada z Maliną',
        'Biała Czekolada z Borówką'
    ],
    tort: [
        'Tort czekoladowy',
        'Tort owocowy',
        'Tort śmietankowy',
        'Tort z kremem mascarpone',
        'Tort z bitą śmietaną',
        'Inny (opisz w uwagach)'
    ]
};

// ============================
// DOM READY
// ============================
document.addEventListener('DOMContentLoaded', function() {
    initMobileMenu();
    initNavbarScroll();
    initScrollAnimations();
    initLightbox();
    initMultiStepForm();
    initSmoothScroll();
    initKeyboardNavigation();
    initCookieBanner();
});

// ============================
// MOBILE MENU
// ============================
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileOverlay = document.getElementById('mobile-overlay');
    const closeMobileMenu = document.getElementById('close-mobile-menu');
    const mobileLinks = document.querySelectorAll('.mobile-link');

    if (!mobileMenuBtn || !mobileMenu) return;

    function openMenu() {
        mobileMenu.classList.add('open');
        mobileOverlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        mobileMenuBtn.setAttribute('aria-expanded', 'true');
    }

    function closeMenu() {
        mobileMenu.classList.remove('open');
        mobileOverlay.classList.add('hidden');
        document.body.style.overflow = '';
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
    }

    mobileMenuBtn.addEventListener('click', openMenu);
    if (closeMobileMenu) closeMobileMenu.addEventListener('click', closeMenu);
    if (mobileOverlay) mobileOverlay.addEventListener('click', closeMenu);
    mobileLinks.forEach(link => link.addEventListener('click', closeMenu));

    // Focus trap for mobile menu (accessibility)
    mobileMenu.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            const focusableElements = mobileMenu.querySelectorAll('a, button');
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (e.shiftKey && document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        }
    });

    // Expose closeMenu for keyboard handler
    window.closeMobileMenuFn = closeMenu;
}

// ============================
// NAVBAR SCROLL EFFECT
// ============================
function initNavbarScroll() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > CONFIG.NAVBAR_SCROLL_THRESHOLD) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    }, { passive: true });
}

// ============================
// SCROLL ANIMATIONS
// ============================
function initScrollAnimations() {
    const animateElements = document.querySelectorAll('.animate-on-scroll');
    if (animateElements.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: CONFIG.INTERSECTION_THRESHOLD,
        rootMargin: CONFIG.INTERSECTION_ROOT_MARGIN
    });

    animateElements.forEach(el => observer.observe(el));
}

// ============================
// LIGHTBOX GALLERY
// ============================
function initLightbox() {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const closeLightboxBtn = document.getElementById('close-lightbox');

    if (!lightbox) return;

    function closeLightbox() {
        lightbox.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Expose openLightbox globally for onclick handlers
    window.openLightbox = function(src) {
        lightboxImg.src = src;
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
    };

    if (closeLightboxBtn) closeLightboxBtn.addEventListener('click', closeLightbox);

    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && lightbox.classList.contains('active')) {
            closeLightbox();
        }
    });
}

// ============================
// MULTI-STEP FORM
// ============================
function initMultiStepForm() {
    const form = document.getElementById('cake-form');
    if (!form) return;

    let currentStep = 1;
    const totalSteps = CONFIG.TOTAL_FORM_STEPS;
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');
    const progressBar = document.getElementById('progress-bar');
    const stepLabel = document.getElementById('step-label');
    const stepPercent = document.getElementById('step-percent');
    const stepIndicators = document.querySelectorAll('.step-indicator');
    const flavorSelect = document.getElementById('flavor-select');

    // Expose preselectCake globally for onclick handlers
    window.preselectCake = function(type, flavor) {
        const typeInput = document.getElementById(`type-${type}`);
        if (typeInput) {
            typeInput.checked = true;
        }
        localStorage.setItem('ohmycake_preselect_flavor', flavor);
        localStorage.setItem('ohmycake_preselect_type', type);
    };

    function updateProgress() {
        const percent = (currentStep / totalSteps) * 100;
        progressBar.style.width = `${percent}%`;
        stepLabel.textContent = `Krok ${currentStep} z ${totalSteps}`;
        stepPercent.textContent = `${Math.round(percent)}%`;

        stepIndicators.forEach((indicator, index) => {
            if (index + 1 <= currentStep) {
                indicator.classList.remove('bg-gray-200', 'text-gray-500');
                indicator.classList.add('bg-accent-pink', 'text-white');
            } else {
                indicator.classList.remove('bg-accent-pink', 'text-white');
                indicator.classList.add('bg-gray-200', 'text-gray-500');
            }
        });
    }

    function showStep(step) {
        document.querySelectorAll('.form-step').forEach((el, index) => {
            el.classList.remove('active');
            if (index + 1 === step) {
                el.classList.add('active');
            }
        });

        prevBtn.classList.toggle('hidden', step === 1);
        nextBtn.classList.toggle('hidden', step === totalSteps);
        submitBtn.classList.toggle('hidden', step !== totalSteps);

        if (step === totalSteps) {
            updateSummary();
        }
    }

    function populateFlavors() {
        const selectedType = document.querySelector('input[name="type"]:checked');
        if (!selectedType) return;

        const type = selectedType.value;
        const options = flavors[type] || [];

        flavorSelect.innerHTML = '<option value="">-- Wybierz smak --</option>';
        options.forEach(flavor => {
            const option = document.createElement('option');
            option.value = flavor;
            option.textContent = flavor;
            flavorSelect.appendChild(option);
        });

        const preselectedFlavor = localStorage.getItem('ohmycake_preselect_flavor');
        const preselectedType = localStorage.getItem('ohmycake_preselect_type');

        if (preselectedFlavor && preselectedType === type) {
            flavorSelect.value = preselectedFlavor;
            localStorage.removeItem('ohmycake_preselect_flavor');
            localStorage.removeItem('ohmycake_preselect_type');
        }
    }

    function showValidationError(message) {
        const errorDiv = document.getElementById('validation-error');
        const errorMessage = document.getElementById('validation-message');
        errorMessage.textContent = message;
        errorDiv.classList.remove('hidden');
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });

        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, CONFIG.VALIDATION_ERROR_TIMEOUT);
    }

    function hideValidationError() {
        const errorDiv = document.getElementById('validation-error');
        if (errorDiv) errorDiv.classList.add('hidden');
    }

    function validateStep() {
        hideValidationError();
        const currentStepEl = document.getElementById(`step-${currentStep}`);
        if (!currentStepEl) return true;

        const requiredInputs = currentStepEl.querySelectorAll('[required]');

        for (const input of requiredInputs) {
            if (input.type === 'radio') {
                const name = input.name;
                const checked = currentStepEl.querySelector(`input[name="${name}"]:checked`);
                if (!checked) {
                    showValidationError('Proszę wybrać jedną z opcji.');
                    return false;
                }
            } else if (!input.value.trim()) {
                input.focus();
                input.classList.add('border-red-400');
                showValidationError('Proszę wypełnić wymagane pole.');
                input.addEventListener('input', () => {
                    input.classList.remove('border-red-400');
                    hideValidationError();
                }, { once: true });
                return false;
            }
        }

        // Additional phone validation (Polish format)
        if (currentStep === CONFIG.TOTAL_FORM_STEPS) {
            const phoneInput = document.getElementById('phone');
            const phone = phoneInput ? phoneInput.value : '';
            if (phone && !CONFIG.PHONE_REGEX.test(phone.replace(/\s/g, ''))) {
                if (phoneInput) phoneInput.focus();
                showValidationError(`Numer telefonu powinien mieć ${CONFIG.MIN_PHONE_DIGITS} cyfr (np. 726 760 700).`);
                return false;
            }
        }

        return true;
    }

    function updateSummary() {
        const summaryContent = document.getElementById('summary-content');
        if (!summaryContent) return;

        const type = document.querySelector('input[name="type"]:checked')?.value || '-';
        const flavor = flavorSelect.value || '-';
        const portions = document.getElementById('portions')?.value || '-';
        const date = document.getElementById('date')?.value || '-';
        const inscription = document.getElementById('inscription')?.value || '-';
        const color = document.getElementById('color')?.value || '-';
        const theme = document.getElementById('theme')?.value || '-';

        const typeLabels = {
            'blacha': 'Blacha Prostokątna (140 zł)',
            'tortownica': 'Tortownica (130 zł)',
            'tort': 'Tort Okolicznościowy (wycena indywidualna)'
        };

        summaryContent.innerHTML = `
            <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-500">Rodzaj:</span>
                <span class="font-medium text-gray-800">${typeLabels[type] || type}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-500">Smak:</span>
                <span class="font-medium text-gray-800">${sanitizeInput(flavor)}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-500">Porcje:</span>
                <span class="font-medium text-gray-800">${sanitizeInput(portions)}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-500">Data odbioru:</span>
                <span class="font-medium text-gray-800">${sanitizeInput(date)}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-500">Napis:</span>
                <span class="font-medium text-gray-800">${sanitizeInput(inscription)}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-500">Kolor:</span>
                <span class="font-medium text-gray-800">${sanitizeInput(color)}</span>
            </div>
            <div class="flex justify-between py-2">
                <span class="text-gray-500">Motyw:</span>
                <span class="font-medium text-gray-800">${sanitizeInput(theme)}</span>
            </div>
        `;
    }

    function saveFormData() {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        localStorage.setItem('ohmycake_form', JSON.stringify(data));
    }

    function loadFormData() {
        const saved = localStorage.getItem('ohmycake_form');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                Object.keys(data).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input) {
                        if (input.type === 'radio') {
                            const radio = form.querySelector(`[name="${key}"][value="${data[key]}"]`);
                            if (radio) radio.checked = true;
                        } else {
                            input.value = data[key];
                        }
                    }
                });

                populateFlavors();
                if (data.flavor) {
                    flavorSelect.value = data.flavor;
                }
            } catch (e) {
                console.error('Error loading form data:', e);
            }
        }
    }

    function setSubmitLoading(isLoading) {
        const submitText = document.getElementById('submit-text');
        const submitLoading = document.getElementById('submit-loading');

        submitBtn.disabled = isLoading;
        if (submitText) submitText.classList.toggle('hidden', isLoading);
        if (submitLoading) submitLoading.classList.toggle('hidden', !isLoading);
    }

    // Event listeners
    nextBtn.addEventListener('click', () => {
        if (!validateStep()) return;

        if (currentStep === 1) {
            populateFlavors();
        }

        currentStep++;
        showStep(currentStep);
        updateProgress();
        saveFormData();
    });

    prevBtn.addEventListener('click', () => {
        currentStep--;
        showStep(currentStep);
        updateProgress();
    });

    // Type radio change
    document.querySelectorAll('input[name="type"]').forEach(radio => {
        radio.addEventListener('change', populateFlavors);
    });

    // Form submission with loading state
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!validateStep()) return;

        setSubmitLoading(true);

        // Collect and SANITIZE form data (XSS prevention)
        const formData = new FormData(form);
        const rawData = Object.fromEntries(formData.entries());
        const data = sanitizeFormData(rawData);

        // Add phone prefix
        data.phone = CONFIG.PHONE_PREFIX + ' ' + data.phone;

        console.log('Form submitted:', data);

        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams(formData).toString()
            });

            if (response.ok) {
                form.classList.add('hidden');
                document.getElementById('success-message').classList.remove('hidden');
                localStorage.removeItem('ohmycake_form');
            } else {
                throw new Error('Form submission failed');
            }
        } catch (error) {
            // Fallback: Open mailto link
            const subject = encodeURIComponent('Zamówienie z Oh My Cake');
            const body = encodeURIComponent(`
Nowe zamówienie z formularza na stronie:

Rodzaj: ${data.type}
Smak: ${data.flavor}
Porcje: ${data.portions || '-'}
Data odbioru: ${data.date}
Napis: ${data.inscription || '-'}
Kolor: ${data.color || '-'}
Motyw: ${data.theme || '-'}

Dane kontaktowe:
Imię: ${data.name}
Telefon: ${data.phone}
Email: ${data.email || '-'}
Miasto: ${data.city || '-'}

Uwagi: ${data.notes || '-'}
            `);

            window.location.href = `mailto:?subject=${subject}&body=${body}`;

            form.classList.add('hidden');
            document.getElementById('success-message').classList.remove('hidden');
            localStorage.removeItem('ohmycake_form');
        } finally {
            setSubmitLoading(false);
        }
    });

    // Set minimum date to today
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
    }

    // Initialize
    loadFormData();
    updateProgress();

    // Check for preselected cake on page load
    const preselectedType = localStorage.getItem('ohmycake_preselect_type');
    if (preselectedType) {
        const typeInput = document.getElementById(`type-${preselectedType}`);
        if (typeInput) {
            typeInput.checked = true;
        }
    }
}

// ============================
// SMOOTH SCROLL
// ============================
function initSmoothScroll() {
    const navbar = document.getElementById('navbar');

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                const navHeight = navbar ? navbar.offsetHeight : 0;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ============================
// KEYBOARD NAVIGATION
// ============================
function initKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            // Close mobile menu with Escape
            if (window.closeMobileMenuFn) {
                window.closeMobileMenuFn();
            }
        }
    });
}

// ============================
// COOKIE BANNER (GDPR)
// ============================
function initCookieBanner() {
    const cookieBanner = document.getElementById('cookie-banner');
    const cookieAccept = document.getElementById('cookie-accept');
    const cookieReject = document.getElementById('cookie-reject');

    if (!cookieBanner) return;

    function checkCookieConsent() {
        const consent = localStorage.getItem('ohmycake_cookie_consent');
        if (!consent) {
            setTimeout(() => {
                cookieBanner.classList.remove('translate-y-full');
            }, CONFIG.COOKIE_BANNER_DELAY);
        }
    }

    if (cookieAccept) {
        cookieAccept.addEventListener('click', () => {
            localStorage.setItem('ohmycake_cookie_consent', 'all');
            cookieBanner.classList.add('translate-y-full');
        });
    }

    if (cookieReject) {
        cookieReject.addEventListener('click', () => {
            localStorage.setItem('ohmycake_cookie_consent', 'essential');
            cookieBanner.classList.add('translate-y-full');
        });
    }

    checkCookieConsent();
}
