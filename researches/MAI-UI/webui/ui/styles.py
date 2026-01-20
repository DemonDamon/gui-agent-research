"""
UI styles and themes for MAI-UI WebUI.
Provides custom CSS, JavaScript enhancements, and theme configuration.
"""

import gradio as gr
from .i18n import t


def get_theme() -> gr.Theme:
    """
    Get custom Gradio theme.
    
    Returns:
        Gradio Theme object
    """
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
    ).set(
        body_background_fill="*neutral_50",
        body_background_fill_dark="*neutral_950",
        block_background_fill="white",
        block_background_fill_dark="*neutral_900",
        block_border_width="1px",
        block_border_color="*neutral_200",
        block_border_color_dark="*neutral_700",
        block_radius="12px",
        block_shadow="0 1px 3px 0 rgb(0 0 0 / 0.1)",
        block_shadow_dark="0 1px 3px 0 rgb(0 0 0 / 0.3)",
        button_primary_background_fill="*primary_500",
        button_primary_background_fill_hover="*primary_600",
        button_primary_text_color="white",
        button_secondary_background_fill="*neutral_100",
        button_secondary_background_fill_dark="*neutral_700",
        input_background_fill="*neutral_50",
        input_background_fill_dark="*neutral_800",
        input_border_color="*neutral_300",
        input_border_color_dark="*neutral_600",
    )


def get_custom_css() -> str:
    """
    Get custom CSS styles for the WebUI.
    
    Returns:
        CSS string
    """
    return """
/* ============ Global Styles ============ */
:root {
    --mai-primary: #3b82f6;
    --mai-primary-dark: #2563eb;
    --mai-secondary: #64748b;
    --mai-success: #22c55e;
    --mai-warning: #f59e0b;
    --mai-error: #ef4444;
    --mai-card-bg: #ffffff;
    --mai-card-bg-dark: #1e293b;
    --mai-border: #e2e8f0;
    --mai-border-dark: #334155;
}

/* ============ Layout ============ */
.gradio-container {
    max-width: 1920px !important;
}

/* Panel styles */
.mai-panel {
    background: var(--mai-card-bg);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    margin-bottom: 12px;
}

.dark .mai-panel {
    background: var(--mai-card-bg-dark);
}

/* ============ Header ============ */
.mai-header {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    color: white;
    padding: 24px 32px;
    border-radius: 12px;
    margin-bottom: 24px;
    text-align: center;
    margin-top: -8px;
}

.mai-header h1 {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 700;
}

.mai-header p {
    margin: 8px 0 0 0;
    opacity: 0.9;
    font-size: 0.95rem;
}

/* ============ Language Switcher ============ */
.lang-switcher-container {
    display: flex !important;
    justify-content: center !important;
    gap: 8px !important;
    margin-bottom: 16px !important;
    padding: 0 !important;
}

.lang-btn {
    min-width: 70px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
    position: relative !important;
}

.lang-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
}

/* Active state (primary variant) - Gradio adds 'primary' class */
.lang-btn.primary,
button.lang-btn.primary {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
    border-color: #2563eb !important;
    box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4) !important;
}

/* Inactive state (secondary variant) */
.lang-btn.secondary,
button.lang-btn.secondary {
    background: #334155 !important;
    color: #94a3b8 !important;
    border-color: #475569 !important;
}

.lang-btn.secondary:hover {
    background: #475569 !important;
    color: #e2e8f0 !important;
    border-color: #64748b !important;
}


/* ============ Export Control Buttons ============ */
.export-control-btn {
    height: 36px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ============ Refresh Buttons ============ */
.refresh-btn {
    min-width: 80px !important;
    height: 36px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.refresh-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}

.refresh-btn:active {
    transform: translateY(0) !important;
}

/* Green refresh button variant */
.refresh-btn-green,
.refresh-btn-green.secondary {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    color: white !important;
    border-color: #16a34a !important;
    box-shadow: 0 2px 6px rgba(34, 197, 94, 0.3) !important;
}

.refresh-btn-green:hover {
    background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
    box-shadow: 0 4px 8px rgba(34, 197, 94, 0.4) !important;
}

/* ============ Status Indicators ============ */
.mai-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}

.mai-status-running {
    background: rgba(34, 197, 94, 0.1);
    color: #16a34a;
}

.mai-status-paused {
    background: rgba(245, 158, 11, 0.1);
    color: #d97706;
}

.mai-status-stopped {
    background: rgba(100, 116, 139, 0.1);
    color: #475569;
}

.mai-status-error {
    background: rgba(239, 68, 68, 0.1);
    color: #dc2626;
}

/* ============ Buttons ============ */
.mai-btn-primary {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.mai-btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}

.mai-btn-success {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    border: none !important;
    color: white !important;
}

.mai-btn-warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
    border: none !important;
    color: white !important;
}

.mai-btn-danger {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    border: none !important;
    color: white !important;
}

/* ============ Chatbot Styles ============ */
.mai-chatbot {
    min-height: 500px;
    max-height: 700px;
}

.mai-chatbot .message {
    border-radius: 12px !important;
    margin: 8px 0 !important;
}

.mai-chatbot .user {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
}

.mai-chatbot .bot {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
}

.dark .mai-chatbot .bot {
    background: #1e293b !important;
    border-color: #334155 !important;
}

/* ============ Image Preview ============ */
.mai-image-preview {
    cursor: pointer;
    transition: transform 0.2s ease;
    border-radius: 8px;
    overflow: hidden;
}

.mai-image-preview:hover {
    transform: scale(1.02);
}

/* Lightbox overlay */
.mai-lightbox {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

.mai-lightbox.active {
    opacity: 1;
    pointer-events: auto;
}

.mai-lightbox img {
    max-width: 90%;
    max-height: 90%;
    object-fit: contain;
    border-radius: 8px;
}

.mai-lightbox-close {
    position: absolute;
    top: 20px;
    right: 20px;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    opacity: 0.8;
    transition: opacity 0.2s;
}

.mai-lightbox-close:hover {
    opacity: 1;
}

/* ============ Accordion ============ */
.mai-accordion {
    border: 1px solid var(--mai-border);
    border-radius: 8px;
    overflow: hidden;
}

/* Style for our custom accordion title */
.accordion-title {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: inherit !important;
    padding: 12px 16px !important;
    margin: 0 !important;
    margin-bottom: 8px !important;
    background: transparent !important;
    border-bottom: 1px solid var(--mai-border) !important;
    display: block !important;
    visibility: visible !important;
}

.dark .accordion-title {
    color: white !important;
    border-bottom-color: #334155 !important;
}

/* For nested accordions with empty label, show the HTML title */
.mai-accordion > .wrap > .form:first-child .accordion-title {
    position: relative;
    z-index: 1;
}

.mai-accordion .label-wrap {
    background: #f8fafc !important;
    padding: 12px 16px !important;
}

.dark .mai-accordion .label-wrap {
    background: #1e293b !important;
}

/* ============ Tabs ============ */
.mai-tabs .tab-nav {
    border-bottom: 2px solid var(--mai-border);
}

.mai-tabs .tab-nav button {
    border: none !important;
    background: transparent !important;
    padding: 12px 20px !important;
    font-weight: 500;
    color: var(--mai-secondary);
    transition: all 0.2s ease;
}

.mai-tabs .tab-nav button.selected {
    color: var(--mai-primary) !important;
    border-bottom: 2px solid var(--mai-primary) !important;
    margin-bottom: -2px;
}

/* ============ Code Editor ============ */
.mai-code-editor {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
}

/* Fix layout shift when content changes */
.mai-code-editor .wrap {
    min-height: 500px !important;
    height: auto !important;
    display: flex !important;
    flex-direction: column !important;
}

.mai-code-editor .wrap > div {
    min-height: 500px !important;
    height: auto !important;
    flex: 1 !important;
}

.mai-code-editor textarea {
    background: #1e1e1e !important;
    color: #d4d4d4 !important;
    border-radius: 8px !important;
    min-height: 500px !important;
    height: auto !important;
}

/* Ensure code editor container maintains stable height */
.mai-code-editor .monaco-editor,
.mai-code-editor .monaco-editor-container {
    min-height: 500px !important;
    height: auto !important;
}

/* Prevent layout shift on content change */
.mai-code-editor .block {
    min-height: 500px !important;
}

.mai-code-editor .form {
    min-height: 500px !important;
}

/* ============ Progress Bar ============ */
.mai-progress {
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    overflow: hidden;
}

.mai-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    border-radius: 4px;
    transition: width 0.3s ease;
}

/* ============ Stats Cards ============ */
.mai-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
}

.mai-stat-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}

.dark .mai-stat-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}

.mai-stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--mai-primary);
}

.mai-stat-label {
    font-size: 0.875rem;
    color: var(--mai-secondary);
    margin-top: 4px;
}

/* ============ Form Elements ============ */
.mai-form-group {
    margin-bottom: 16px;
}

.mai-form-label {
    display: block;
    font-weight: 500;
    margin-bottom: 6px;
    color: #374151;
}

.dark .mai-form-label {
    color: #d1d5db;
}

/* ============ Dropdown ============ */
.mai-dropdown {
    border-radius: 8px !important;
}

.mai-dropdown .wrap {
    border-radius: 8px !important;
}

/* ============ Animation ============ */
@keyframes mai-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.mai-loading {
    animation: mai-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes mai-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.mai-spinner {
    animation: mai-spin 1s linear infinite;
}

/* ============ Responsive ============ */
@media (max-width: 768px) {
    .mai-header h1 {
        font-size: 1.25rem;
    }
    
    .mai-stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* ============ Scrollbar ============ */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}

.dark ::-webkit-scrollbar-track {
    background: #1e293b;
}

.dark ::-webkit-scrollbar-thumb {
    background: #475569;
}

.dark ::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}
"""


def get_custom_js() -> str:
    """
    Get custom JavaScript for UI enhancements.
    
    Returns:
        JavaScript string
    """
    return """
<script>
// MAI-UI WebUI JavaScript Enhancements

(function() {
    'use strict';
    
    // ============ Lightbox ============
    function initLightbox() {
        // Create lightbox container
        if (!document.querySelector('.mai-lightbox')) {
            const lightbox = document.createElement('div');
            lightbox.className = 'mai-lightbox';
            lightbox.innerHTML = `
                <span class="mai-lightbox-close">&times;</span>
                <img src="" alt="Preview">
            `;
            document.body.appendChild(lightbox);
            
            // Close on click
            lightbox.addEventListener('click', (e) => {
                if (e.target === lightbox || e.target.classList.contains('mai-lightbox-close')) {
                    lightbox.classList.remove('active');
                }
            });
            
            // Close on Escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && lightbox.classList.contains('active')) {
                    lightbox.classList.remove('active');
                }
            });
        }
        
        // Attach click handlers to chatbot images
        document.addEventListener('click', (e) => {
            const img = e.target.closest('.mai-chatbot img, .chatbot img');
            if (img && img.src) {
                const lightbox = document.querySelector('.mai-lightbox');
                const lightboxImg = lightbox.querySelector('img');
                lightboxImg.src = img.src;
                lightbox.classList.add('active');
            }
        });
    }
    
    // ============ Auto-scroll ============
    let userScrolled = false;
    let scrollTimeout = null;
    
    function initAutoScroll() {
        const chatbots = document.querySelectorAll('.chatbot, .mai-chatbot');
        
        chatbots.forEach(chatbot => {
            const container = chatbot.querySelector('.wrap') || chatbot;
            
            // Detect user scroll
            container.addEventListener('scroll', () => {
                const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
                if (!isAtBottom) {
                    userScrolled = true;
                    clearTimeout(scrollTimeout);
                    scrollTimeout = setTimeout(() => {
                        userScrolled = false;
                    }, 3000);
                } else {
                    userScrolled = false;
                }
            });
        });
        
        // Auto-scroll on new messages
        const observer = new MutationObserver((mutations) => {
            if (!userScrolled) {
                mutations.forEach(mutation => {
                    if (mutation.addedNodes.length > 0) {
                        const chatbot = mutation.target.closest('.chatbot, .mai-chatbot');
                        if (chatbot) {
                            const container = chatbot.querySelector('.wrap') || chatbot;
                            container.scrollTop = container.scrollHeight;
                        }
                    }
                });
            }
        });
        
        chatbots.forEach(chatbot => {
            observer.observe(chatbot, { childList: true, subtree: true });
        });
    }
    
    // ============ Keyboard Shortcuts ============
    function initShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter to submit
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const activeElement = document.activeElement;
                if (activeElement && (activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'INPUT')) {
                    // Find the submit button in the same form/container
                    const container = activeElement.closest('.block, .form, .row');
                    if (container) {
                        const submitBtn = container.querySelector('button[type="submit"], button.primary');
                        if (submitBtn) {
                            submitBtn.click();
                        }
                    }
                }
            }
        });
    }
    
    // ============ Theme Detection ============
    function initTheme() {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.classList.toggle('dark', prefersDark);
        
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            document.documentElement.classList.toggle('dark', e.matches);
        });
    }
    
    // ============ Notifications ============
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `mai-notification mai-notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Export to global scope
    window.maiUI = {
        showNotification,
    };
    
    // ============ Language Update ============
    function updateLanguageLabels(lang = 'en') {
        // Translation mappings
        const translations = {
            'en': {
                accordions: {
                    '设备管理': 'Device Management',
                    '任务控制': 'Task Control',
                    '自动运行设置': 'Auto-run Settings',
                    '用户反馈': 'User Feedback',
                    '无线连接': 'Wireless Connection',
                    '模型配置': 'Model Configuration',
                    'API设置': 'API Settings',
                    '管理提供商': 'Manage Providers',
                    '模板变量': 'Template Variables',
                    '预览输出': 'Preview Output',
                    '高级选项': 'Advanced Options',
                    '导出统计': 'Export Statistics',
                },
                tabs: {
                    '提示词配置': 'Prompt Configuration',
                    '数据导出': 'Data Export',
                },
            },
            'zh': {
                accordions: {
                    'Device Management': '设备管理',
                    'Task Control': '任务控制',
                    'Auto-run Settings': '自动运行设置',
                    'User Feedback': '用户反馈',
                    'Wireless Connection': '无线连接',
                    'Model Configuration': '模型配置',
                    'API Settings': 'API设置',
                    'Manage Providers': '管理提供商',
                    'Template Variables': '模板变量',
                    'Preview Output': '预览输出',
                    'Advanced Options': '高级选项',
                    'Export Statistics': '导出统计',
                },
                tabs: {
                    'Prompt Configuration': '提示词配置',
                    'Data Export': '数据导出',
                },
            },
        };
        
        const map = translations[lang] || translations['en'];
        
        function updateAccordions() {
            console.log('[MAI-UI] Updating accordions, lang:', lang);
            
            // Update Accordion labels - focus on .label-wrap which contains the clickable title
            const accordionSelectors = [
                '.mai-accordion .label-wrap',
                '.mai-accordion label',
                '.mai-accordion button',
                '[class*="accordion"] .label-wrap',
                '[class*="accordion"] label',
            ];
            
            accordionSelectors.forEach(selector => {
                try {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(element => {
                        const text = element.textContent.trim();
                        if (map.accordions[text]) {
                            console.log('[MAI-UI] Updating accordion:', text, '->', map.accordions[text]);
                            element.textContent = map.accordions[text];
                            // Also update child text nodes
                            const walker = document.createTreeWalker(
                                element,
                                NodeFilter.SHOW_TEXT,
                                null
                            );
                            let textNode;
                            while (textNode = walker.nextNode()) {
                                if (textNode.textContent.trim() === text) {
                                    textNode.textContent = map.accordions[text];
                                }
                            }
                        }
                    });
                } catch (e) {
                    console.warn('[MAI-UI] Error with selector:', selector, e);
                }
            });
            
            // Also try to find by traversing all elements
            const allElements = document.querySelectorAll('.mai-accordion *');
            Object.keys(map.accordions).forEach(englishText => {
                const chineseText = map.accordions[englishText];
                allElements.forEach(element => {
                    if (element.textContent && element.textContent.trim() === englishText) {
                        console.log('[MAI-UI] Found and updating:', englishText, '->', chineseText);
                        element.textContent = chineseText;
                    }
                });
            });
        }
        
        function updateTabs() {
            // Try multiple selectors for Gradio tabs
            const selectors = [
                '.tab-nav button',
                '.tab-nav label',
                '[role="tab"]',
                '[class*="tab"] button',
                '.gr-tabs button',
                '.gr-tabs label',
                'button[class*="tab"]',
                'label[class*="tab"]',
                '.tabs button',
                '.tabs label',
            ];
            
            selectors.forEach(selector => {
                try {
                    const tabs = document.querySelectorAll(selector);
                    tabs.forEach(tab => {
                        const text = tab.textContent.trim();
                        if (map.tabs[text]) {
                            tab.textContent = map.tabs[text];
                            // Also update innerHTML if it contains the text
                            if (tab.innerHTML && tab.innerHTML.includes(text)) {
                                tab.innerHTML = tab.innerHTML.replace(text, map.tabs[text]);
                            }
                        }
                        // Also check child elements
                        const children = tab.querySelectorAll('span, div');
                        children.forEach(child => {
                            const childText = child.textContent.trim();
                            if (map.tabs[childText]) {
                                child.textContent = map.tabs[childText];
                            }
                        });
                    });
                } catch (e) {
                    console.warn('Error updating tabs with selector:', selector, e);
                }
            });
            
            // Also try to find tabs by their aria-label or data attributes
            try {
                const allButtons = document.querySelectorAll('button');
                allButtons.forEach(btn => {
                    const text = btn.textContent.trim();
                    if (map.tabs[text]) {
                        btn.textContent = map.tabs[text];
                    }
                });
            } catch (e) {
                console.warn('Error updating tabs by button text:', e);
            }
        }
        
        // Update immediately
        updateAccordions();
        updateTabs();
        
        // Retry multiple times with delays to catch dynamically loaded elements
        [100, 300, 500, 1000].forEach(delay => {
            setTimeout(() => {
                updateAccordions();
                updateTabs();
            }, delay);
        });
    }
    
    // ============ Initialize ============
    function init() {
        initLightbox();
        initAutoScroll();
        initShortcuts();
        initTheme();
        console.log('[MAI-UI] JavaScript enhancements loaded');
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Re-initialize on Gradio updates
    const gradioObserver = new MutationObserver(() => {
        initAutoScroll();
    });
    
    gradioObserver.observe(document.body, { childList: true, subtree: true });
    
    // Listen for language change events
    window.addEventListener('languageChanged', (e) => {
        const lang = e.detail?.lang || 'en';
        console.log('[MAI-UI] Language changed event received, lang:', lang);
        // Update immediately
        updateLanguageLabels(lang);
        // Retry multiple times with delays to catch all elements
        [50, 100, 200, 300, 500, 800, 1000, 1500, 2000].forEach(delay => {
            setTimeout(() => {
                console.log('[MAI-UI] Retrying language update, delay:', delay);
                updateLanguageLabels(lang);
            }, delay);
        });
    });
    
    // Also listen for Gradio component updates
    let updateTimeout;
    const gradioUpdateObserver = new MutationObserver(() => {
        const currentLang = document.documentElement.getAttribute('data-lang') || 'en';
        // Debounce updates
        clearTimeout(updateTimeout);
        updateTimeout = setTimeout(() => {
            updateLanguageLabels(currentLang);
        }, 100);
    });
    
    gradioUpdateObserver.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
    });
})();
</script>

<style>
@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
}
</style>
"""


def get_header_html() -> str:
    """
    Get HTML for the header component.
    
    Returns:
        HTML string
    """
    return f"""
<div class="mai-header">
    <h1>{t('header.title')}</h1>
    <p>{t('header.subtitle')}</p>
</div>
"""


def get_status_html(status: str, status_type: str = "stopped") -> str:
    """
    Get HTML for status indicator.
    
    Args:
        status: Status text
        status_type: One of "running", "paused", "stopped", "error"
        
    Returns:
        HTML string
    """
    icons = {
        "running": "🟢",
        "paused": "🟡",
        "stopped": "⚪",
        "error": "🔴",
    }
    icon = icons.get(status_type, "⚪")
    return f'<div class="mai-status mai-status-{status_type}">{icon} {status}</div>'


def get_stats_html(stats: dict) -> str:
    """
    Get HTML for statistics display.
    
    Args:
        stats: Dictionary of stat_name -> stat_value
        
    Returns:
        HTML string
    """
    cards = []
    for label, value in stats.items():
        cards.append(f"""
        <div class="mai-stat-card">
            <div class="mai-stat-value">{value}</div>
            <div class="mai-stat-label">{label}</div>
        </div>
        """)
    
    return f'<div class="mai-stats-grid">{"".join(cards)}</div>'
