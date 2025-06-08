/**
 * Admin Confirmation Dialogs using SweetAlert2
 * 
 * This script replaces the default browser confirm dialogs with SweetAlert2 dialogs
 * for better user experience and consistent styling with the rest of the application.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all forms with confirmation dialogs
    const confirmForms = document.querySelectorAll('form[onsubmit^="return confirm"]');
    
    confirmForms.forEach(form => {
        // Extract the confirmation message from the onsubmit attribute
        const onsubmitAttr = form.getAttribute('onsubmit');
        let confirmMessage = '';
        
        if (onsubmitAttr) {
            // Extract the message between single quotes
            const match = onsubmitAttr.match(/confirm\('(.+?)'\)/);
            if (match && match[1]) {
                confirmMessage = match[1];
            }
        }
        
        // Remove the original onsubmit attribute
        form.removeAttribute('onsubmit');
        
        // Add a new event listener for form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Determine the type of action based on the form action URL
            const actionUrl = form.getAttribute('action');
            let icon = 'warning';
            let confirmButtonText = 'Yes, proceed';
            let confirmButtonColor = '#d33';
            let title = 'Are you sure?';
            let html = confirmMessage;
            
            // Check if this is a delete action
            const isDelete = actionUrl.includes('delete') || actionUrl.includes('reset');
            
            if (isDelete) {
                // Set default delete styling
                icon = 'warning';
                confirmButtonText = 'Yes, delete';
                
                // Check for specific action types to customize dialog
                if (actionUrl.includes('reset_all')) {
                    title = 'Warning: Delete All Content';
                    confirmButtonColor = '#dc3545'; // Bootstrap danger color
                    html = `<div class="text-danger">
                              <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                              <p>${confirmMessage}</p>
                            </div>`;
                } else if (actionUrl.includes('reset_photos')) {
                    title = 'Delete All Photos';
                    html = `<div>
                              <i class="fas fa-images fa-2x mb-3 text-danger"></i>
                              <p>${confirmMessage}</p>
                            </div>`;
                } else if (actionUrl.includes('reset_audio')) {
                    title = 'Delete All Audio Messages';
                    html = `<div>
                              <i class="fas fa-microphone-alt fa-2x mb-3 text-danger"></i>
                              <p>${confirmMessage}</p>
                            </div>`;
                } else if (actionUrl.includes('reset_messages')) {
                    title = 'Delete All Guestbook Messages';
                    html = `<div>
                              <i class="fas fa-book-open fa-2x mb-3 text-danger"></i>
                              <p>${confirmMessage}</p>
                            </div>`;
                } else if (actionUrl.includes('delete_photo')) {
                    title = 'Delete Photo';
                    html = `<div>
                              <i class="fas fa-image fa-2x mb-3 text-warning"></i>
                              <p>${confirmMessage}</p>
                            </div>`;
                } else if (actionUrl.includes('delete_audio')) {
                    title = 'Delete Audio Message';
                    html = `<div>
                              <i class="fas fa-microphone fa-2x mb-3 text-warning"></i>
                              <p>${confirmMessage}</p>
                            </div>`;
                } else if (actionUrl.includes('delete_message')) {
                    title = 'Delete Message';
                    html = `<div>
                              <i class="fas fa-comment fa-2x mb-3 text-warning"></i>
                              <p>${confirmMessage}</p>
                            </div>`;
                }
            }
            
            // Show SweetAlert2 confirmation dialog
            Swal.fire({
                title: title,
                html: html,
                icon: icon,
                showCancelButton: true,
                confirmButtonColor: confirmButtonColor,
                cancelButtonColor: '#6c757d', // Bootstrap secondary color
                confirmButtonText: confirmButtonText,
                cancelButtonText: 'Cancel',
                reverseButtons: true,
                focusCancel: true,
                customClass: {
                    confirmButton: 'btn btn-danger',
                    cancelButton: 'btn btn-secondary'
                },
                buttonsStyling: true
            }).then((result) => {
                if (result.isConfirmed) {
                    // If confirmed, show a brief loading state
                    Swal.fire({
                        title: 'Processing...',
                        text: 'Your request is being processed.',
                        icon: 'info',
                        showConfirmButton: false,
                        allowOutsideClick: false,
                        willOpen: () => {
                            Swal.showLoading();
                        },
                        timer: 800,
                        timerProgressBar: true
                    }).then(() => {
                        // Submit the form after the brief loading state
                        form.submit();
                    });
                }
            });
        });
    });
});