// Main JavaScript file for PortalShare

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add heart icon animation to navbar brand
    const navbarBrand = document.querySelector('.navbar-brand');
    if (navbarBrand) {
        const heartIcon = navbarBrand.querySelector('.fa-heart');
        if (heartIcon) {
            heartIcon.classList.add('heart-icon');
        }
    }

    // Add hover effect to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.classList.add('btn-hover-effect');
    });

    // Print QR codes functionality
    const printQRBtn = document.getElementById('printQRCodes');
    if (printQRBtn) {
        printQRBtn.addEventListener('click', function() {
            window.print();
        });
    }

    // Copy link to clipboard functionality
    const copyLinkBtns = document.querySelectorAll('.copy-link');
    copyLinkBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const link = this.getAttribute('data-link');
            navigator.clipboard.writeText(link).then(() => {
                // Show success message
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check me-2"></i> Copied!';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Image preview before upload
    const photoInput = document.getElementById('photo');
    const photoPreview = document.getElementById('photoPreview');
    if (photoInput && photoPreview) {
        photoInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    photoPreview.src = e.target.result;
                    photoPreview.classList.remove('d-none');
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Character counter for textarea
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        const counter = document.createElement('div');
        counter.className = 'form-text text-end';
        counter.innerHTML = `0/${textarea.getAttribute('maxlength')} characters`;
        textarea.parentNode.appendChild(counter);

        textarea.addEventListener('input', function() {
            counter.innerHTML = `${this.value.length}/${this.getAttribute('maxlength')} characters`;
        });
    });
}); 