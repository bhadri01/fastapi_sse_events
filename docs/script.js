/**
 * FastAPI SSE Events - Documentation Scripts
 * Interactive features for the documentation site
 */

// ======================
// Theme Toggle
// ======================
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // Load saved theme or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('#themeToggle i');
    if (theme === 'dark') {
        icon.className = 'fas fa-sun';
    } else {
        icon.className = 'fas fa-moon';
    }
}

// ======================
// Mobile Menu Toggle
// ======================
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    if (!mobileMenuBtn) return;

    mobileMenuBtn.addEventListener('click', () => {
        mobileMenuBtn.classList.toggle('active');
        sidebar.classList.toggle('active');
    });

    // Close sidebar when clicking a link (mobile)
    const sidebarLinks = sidebar.querySelectorAll('a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                mobileMenuBtn.classList.remove('active');
                sidebar.classList.remove('active');
            }
        });
    });

    // Close sidebar when clicking outside (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                mobileMenuBtn.classList.remove('active');
                sidebar.classList.remove('active');
            }
        }
    });
}

// ======================
// Active Navigation Highlighting
// ======================
function initActiveNavigation() {
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
    const sections = document.querySelectorAll('.section');

    // Highlight active section on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;

                // Update sidebar
                sidebarLinks.forEach(link => {
                    if (link.getAttribute('href') === `#${id}`) {
                        link.classList.add('active');
                    } else {
                        link.classList.remove('active');
                    }
                });

                // Update TOC
                updateTOCActive(id);
            }
        });
    }, {
        rootMargin: '-20% 0px -70% 0px'
    });

    sections.forEach(section => observer.observe(section));
}

// ======================
// Table of Contents (Right Sidebar)
// ======================
function updateTOCActive(sectionId) {
    const tocLinks = document.querySelectorAll('.toc-link');
    tocLinks.forEach(link => {
        if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// ======================
// Code Copy Buttons
// ======================
function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const codeBlock = btn.closest('.code-block');
            const codeElement = codeBlock.querySelector('code');
            const text = codeElement.textContent;

            try {
                await navigator.clipboard.writeText(text);

                // Visual feedback
                const originalHTML = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btn.style.color = 'var(--accent-success)';

                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.style.color = '';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
                btn.innerHTML = '<i class="fas fa-times"></i> Failed';
                btn.style.color = 'var(--accent-error)';

                setTimeout(() => {
                    btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    btn.style.color = '';
                }, 2000);
            }
        });
    });
}

// ======================
// Search Functionality
// ======================
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    const sidebarNav = document.querySelector('.sidebar-nav');
    const navSections = sidebarNav.querySelectorAll('.nav-section');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();

        if (query === '') {
            // Reset: show all
            navSections.forEach(section => {
                section.style.display = 'block';
                const links = section.querySelectorAll('li');
                links.forEach(li => li.style.display = 'block');
            });
            return;
        }

        // Filter links
        navSections.forEach(section => {
            const links = section.querySelectorAll('li');
            let hasVisibleLinks = false;

            links.forEach(li => {
                const linkText = li.textContent.toLowerCase();
                if (linkText.includes(query)) {
                    li.style.display = 'block';
                    hasVisibleLinks = true;
                } else {
                    li.style.display = 'none';
                }
            });

            // Hide section if no matching links
            section.style.display = hasVisibleLinks ? 'block' : 'none';
        });
    });

    // Clear search on Escape
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
            searchInput.blur();
        }
    });
}

// ======================
// Smooth Scroll Enhancement
// ======================
function initSmoothScroll() {
    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            const target = document.querySelector(href);

            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Update URL without jumping
                history.pushState(null, null, href);
            }
        });
    });
}

// ======================
// Highlight Current Section on Load
// ======================
function highlightCurrentSection() {
    const hash = window.location.hash;
    if (hash) {
        const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
        sidebarLinks.forEach(link => {
            if (link.getAttribute('href') === hash) {
                link.classList.add('active');
            }
        });
        updateTOCActive(hash.substring(1));
    }
}

// ======================
// External Link Icons
// ======================
function initExternalLinks() {
    const links = document.querySelectorAll('a[href^="http"]');
    links.forEach(link => {
        if (!link.hostname.includes(window.location.hostname)) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
}

// ======================
// Keyboard Shortcuts
// ======================
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('searchInput').focus();
        }

        // Ctrl/Cmd + /: Toggle theme
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            document.getElementById('themeToggle').click();
        }
    });
}

// ======================
// Code Block Language Labels
// ======================
function enhanceCodeBlocks() {
    document.querySelectorAll('pre code[class*="language-"]').forEach(code => {
        const language = code.className.match(/language-(\w+)/);
        if (language) {
            const pre = code.parentElement;
            pre.setAttribute('data-language', language[1]);
        }
    });
}

// ======================
// "Back to Top" Button
// ======================
function initBackToTop() {
    // Create button dynamically
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.setAttribute('aria-label', 'Back to top');
    backToTopBtn.style.cssText = `
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background-color: var(--accent-primary);
    color: white;
    border: none;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
    z-index: 100;
  `;

    document.body.appendChild(backToTopBtn);

    // Show/hide on scroll
    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            backToTopBtn.style.display = 'flex';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });

    // Scroll to top on click
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Hover effect
    backToTopBtn.addEventListener('mouseenter', () => {
        backToTopBtn.style.transform = 'translateY(-4px)';
        backToTopBtn.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.4)';
    });

    backToTopBtn.addEventListener('mouseleave', () => {
        backToTopBtn.style.transform = 'translateY(0)';
        backToTopBtn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
    });
}

// ======================
// Analytics Event Tracking (Optional)
// ======================
function trackEvent(category, action, label) {
    // Integrate with your analytics tool
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            event_category: category,
            event_label: label
        });
    }
}

// Track code copies
function trackCodeCopies() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const codeBlock = btn.closest('.code-block');
            const language = codeBlock.querySelector('code').className.match(/language-(\w+)/);
            trackEvent('Code', 'Copy', language ? language[1] : 'unknown');
        });
    });
}

// ======================
// Print Styles Helper
// ======================
function initPrintStyles() {
    window.addEventListener('beforeprint', () => {
        // Expand all collapsed sections for printing
        document.querySelectorAll('details').forEach(details => {
            details.setAttribute('open', '');
        });
    });
}

// ======================
// Initialize All Features
// ======================
function init() {
    // Wait for DOM to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
        return;
    }

    console.log('🚀 Initializing FastAPI SSE Events Documentation');

    try {
        initThemeToggle();
        initMobileMenu();
        initActiveNavigation();
        initCopyButtons();
        initSearch();
        initSmoothScroll();
        initExternalLinks();
        initKeyboardShortcuts();
        enhanceCodeBlocks();
        initBackToTop();
        initPrintStyles();
        highlightCurrentSection();

        // Optional: Analytics
        // trackCodeCopies();

        console.log('✅ Documentation initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing documentation:', error);
    }
}

// Auto-initialize
init();

// ======================
// Service Worker (Optional - for offline support)
// ======================
if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
    window.addEventListener('load', () => {
        // Uncomment to enable offline support
        // navigator.serviceWorker.register('/sw.js')
        //   .then(reg => console.log('Service Worker registered'))
        //   .catch(err => console.log('Service Worker registration failed', err));
    });
}

// Export for potential external use
window.DocsAPI = {
    updateTOCActive,
    trackEvent,
    version: '1.0.0'
};
