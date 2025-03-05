/**
 * Administrative panel JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin layout script loaded');
    
    // Fix layout issues by ensuring proper visibility
    const sidebar = document.querySelector('.sidebar');
    const contentWrapper = document.querySelector('.content-wrapper');
    const pageContent = document.getElementById('page-content');
    
    if (sidebar && contentWrapper) {
        // Make sure content is visible
        contentWrapper.style.display = 'block';
        
        // Toggle sidebar function
        const sidebarToggle = document.getElementById('sidebarToggleTop');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('toggled');
                contentWrapper.classList.toggle('expanded');
            });
        }
    }
    
    // Check if page content exists and has actual content
    if (pageContent) {
        console.log('Page content found with ' + pageContent.childElementCount + ' child elements');
        if (pageContent.childElementCount === 0) {
            pageContent.innerHTML = '<div class="alert alert-warning">No content found. Please check template inheritance.</div>';
        }
    } else {
        console.error('Page content element not found!');
    }

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add active class to nav items based on URL and highlight parent groups
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.sidebar .list-group-item');
    
    navItems.forEach(function(item) {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
            
            // Find parent group and add active class
            const parentGroup = item.closest('.sidebar-group');
            if (parentGroup) {
                parentGroup.classList.add('active-group');
                
                // If this is a submenu item, expand the parent menu
                const parentSubmenu = item.closest('.sidebar-submenu');
                if (parentSubmenu) {
                    parentSubmenu.classList.add('show');
                    const parentToggle = parentSubmenu.previousElementSibling;
                    if (parentToggle && parentToggle.classList.contains('menu-toggle')) {
                        parentToggle.classList.remove('collapsed');
                    }
                }
            }
        }
    });
    
    // Setup collapsible menu toggles
    const menuToggles = document.querySelectorAll('.menu-toggle');
    menuToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.toggle('collapsed');
            const targetId = this.getAttribute('data-bs-target');
            const target = document.querySelector(targetId);
            if (target) {
                target.classList.toggle('show');
            }
        });
    });
    
    // Mobile sidebar behavior - show tooltips on hover when collapsed
    if (window.innerWidth <= 768) {
        navItems.forEach(function(item) {
            const text = item.querySelector('span').textContent;
            item.setAttribute('title', text);
            item.setAttribute('data-bs-toggle', 'tooltip');
            item.setAttribute('data-bs-placement', 'right');
        });
        
        // Reinitialize tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Points-specific functionality
    const redeemButtons = document.querySelectorAll('.redeem-btn');
    if (redeemButtons.length > 0) {
        redeemButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Disable button while processing
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                // Submit the form (parent of the button)
                this.closest('form').submit();
            });
        });
    }
});
