/* ========================================
   Portfolio - Main JavaScript
   ======================================== */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize all modules
    initAOS();
    initThemeToggle();
    initNavbar();
    initTypingAnimation();
    initSkillBars();
    initProjectFilter();
    initProjectsCarousel();
    initContactForm();
    initBackToTop();
    initSmoothScroll();
});

/* ========================================
   AOS (Animate On Scroll) Init
   ======================================== */
function initAOS() {
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true,
        offset: 80,
    });
}

/* ========================================
   Dark / Light Theme Toggle
   ======================================== */
function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    const icon = document.getElementById('themeIcon');
    if (!toggle || !icon) return;

    // Load saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(icon, savedTheme);

    toggle.addEventListener('click', function () {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(icon, next);
    });
}

function updateThemeIcon(icon, theme) {
    icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

/* ========================================
   Navbar Scroll Effect
   ======================================== */
function initNavbar() {
    const navbar = document.getElementById('mainNav');
    if (!navbar) return;

    function onScroll() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Update active nav link based on scroll position
        updateActiveNavLink();
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // Close mobile menu on link click
    document.querySelectorAll('.nav-link').forEach(function (link) {
        link.addEventListener('click', function () {
            var collapse = document.getElementById('navbarNav');
            if (collapse && collapse.classList.contains('show')) {
                var bsCollapse = bootstrap.Collapse.getInstance(collapse);
                if (bsCollapse) bsCollapse.hide();
            }
        });
    });
}

function updateActiveNavLink() {
    var sections = document.querySelectorAll('section[id]');
    var navLinks = document.querySelectorAll('.nav-link');
    var scrollPos = window.scrollY + 120;

    sections.forEach(function (section) {
        var top = section.offsetTop;
        var bottom = top + section.offsetHeight;
        var id = section.getAttribute('id');

        navLinks.forEach(function (link) {
            var href = link.getAttribute('href');
            if (href && href.includes('#' + id)) {
                if (scrollPos >= top && scrollPos < bottom) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            }
        });
    });
}

/* ========================================
   Typing Animation
   ======================================== */
function initTypingAnimation() {
    var el = document.getElementById('typed-text');
    if (!el) return;

    var texts = window.typingTexts || ['Data Analyst', 'Web Developer', 'CSE Graduate'];
    var textIndex = 0;
    var charIndex = 0;
    var isDeleting = false;
    var typeSpeed = 100;

    function type() {
        var current = texts[textIndex];

        if (isDeleting) {
            el.textContent = current.substring(0, charIndex - 1);
            charIndex--;
        } else {
            el.textContent = current.substring(0, charIndex + 1);
            charIndex++;
        }

        var speed = typeSpeed;

        if (!isDeleting && charIndex === current.length) {
            speed = 2000; // Pause at end
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            textIndex = (textIndex + 1) % texts.length;
            speed = 500; // Pause before typing next
        } else if (isDeleting) {
            speed = 50;
        }

        setTimeout(type, speed);
    }

    type();
}

/* ========================================
   Skill Bars Animation (Intersection Observer)
   ======================================== */
function initSkillBars() {
    var bars = document.querySelectorAll('.skill-progress');
    if (!bars.length) return;

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                var bar = entry.target;
                var width = bar.getAttribute('data-width');
                bar.style.width = width + '%';
                observer.unobserve(bar);
            }
        });
    }, { threshold: 0.3 });

    bars.forEach(function (bar) {
        observer.observe(bar);
    });
}

/* ========================================
   Project Category Filter
   ======================================== */
function initProjectFilter() {
    var filterBtns = document.querySelectorAll('.filter-btn');
    var cards = document.querySelectorAll('.project-card-wrapper');
    if (!filterBtns.length || !cards.length) return;

    var viewport = document.getElementById('projectsViewport');

    // Initialize state for consistent transitions
    cards.forEach(function (card) {
        card.classList.add('show');
        card.classList.remove('hidden');
        card.style.display = '';
        card.setAttribute('aria-hidden', 'false');
    });

    filterBtns.forEach(function (btn) {
        btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
    });

    filterBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            // Update active button
            filterBtns.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');

            filterBtns.forEach(function (b) {
                b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
            });

            var filter = (btn.getAttribute('data-filter') || 'all').trim().toLowerCase();

            cards.forEach(function (card) {
                if (card._hideTimer) {
                    clearTimeout(card._hideTimer);
                    card._hideTimer = null;
                }

                var category = (card.getAttribute('data-category') || '').trim().toLowerCase();
                if (!category) category = 'other';

                if (filter === 'all' || category === filter) {
                    card.style.display = '';
                    requestAnimationFrame(function () {
                        card.classList.remove('hidden');
                        card.classList.add('show');
                    });

                    // AOS may leave elements at opacity:0; ensure visible when filtering
                    card.classList.add('aos-animate');
                    card.setAttribute('aria-hidden', 'false');
                } else {
                    card.classList.add('hidden');
                    card.classList.remove('show');
                    card.setAttribute('aria-hidden', 'true');
                    card._hideTimer = setTimeout(function () {
                        if (card.classList.contains('hidden')) {
                            card.style.display = 'none';
                        }
                    }, 230);
                }
            });

            if (viewport) {
                viewport.scrollTo({ left: 0, behavior: 'smooth' });
            }

            if (window.AOS && typeof window.AOS.refresh === 'function') {
                window.AOS.refresh();
            }
        });
    });
}

/* ========================================
   Projects Carousel (Left/Right Nav)
   ======================================== */
function initProjectsCarousel() {
    var viewport = document.getElementById('projectsViewport');
    var prev = document.getElementById('projectsPrev');
    var next = document.getElementById('projectsNext');
    if (!viewport || !prev || !next) return;

    function getScrollAmount() {
        // Scroll about one card width (fallback to viewport width)
        var card = viewport.querySelector('.project-card-wrapper:not([style*="display: none"])');
        if (card) {
            var rect = card.getBoundingClientRect();
            return Math.max(260, Math.round(rect.width + 20));
        }
        return Math.max(260, Math.round(viewport.clientWidth * 0.85));
    }

    prev.addEventListener('click', function () {
        viewport.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' });
    });

    next.addEventListener('click', function () {
        viewport.scrollBy({ left: getScrollAmount(), behavior: 'smooth' });
    });
}

/* ========================================
   Contact Form (AJAX Submission)
   ======================================== */
function initContactForm() {
    var form = document.getElementById('contactForm');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        var submitBtn = document.getElementById('contactSubmitBtn');
        var alertDiv = document.getElementById('contactAlert');
        var originalText = submitBtn.innerHTML;

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';

        var formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                alertDiv.innerHTML = '<div class="alert alert-success">' +
                    '<i class="fas fa-check-circle me-2"></i>' + data.message + '</div>';
                form.reset();
            } else {
                var errorMsg = 'Please check the form and try again.';
                if (data.errors) {
                    var errors = [];
                    for (var field in data.errors) {
                        errors.push(data.errors[field].join(', '));
                    }
                    errorMsg = errors.join('. ');
                }
                alertDiv.innerHTML = '<div class="alert alert-danger">' +
                    '<i class="fas fa-exclamation-circle me-2"></i>' + errorMsg + '</div>';
            }
            alertDiv.style.display = 'block';
        })
        .catch(function () {
            alertDiv.innerHTML = '<div class="alert alert-danger">' +
                '<i class="fas fa-exclamation-circle me-2"></i>Something went wrong. Please try again later.</div>';
            alertDiv.style.display = 'block';
        })
        .finally(function () {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
    });
}

/* ========================================
   Back to Top Button
   ======================================== */
function initBackToTop() {
    var btn = document.getElementById('backToTop');
    if (!btn) return;

    window.addEventListener('scroll', function () {
        if (window.scrollY > 400) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, { passive: true });

    btn.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/* ========================================
   Smooth Scroll for Anchor Links
   ======================================== */
function initSmoothScroll() {
    document.querySelectorAll('a[href*="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var href = this.getAttribute('href');
            // Only handle same-page hash links
            if (href.startsWith('#') || (href.includes('#') && href.split('#')[0] === '')) {
                var targetId = href.split('#')[1];
                if (!targetId) return;
                var target = document.getElementById(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
}
