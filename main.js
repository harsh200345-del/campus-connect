document.addEventListener('DOMContentLoaded', () => {
    // Bookmark Toggle Handler
    document.querySelectorAll('.btn-bookmark-toggle').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const oppId = button.getAttribute('data-opp-id');
            if (!oppId) return;

            try {
                const response = await fetch(`/bookmark/toggle/${oppId}`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    const icon = button.querySelector('i');
                    if (data.bookmarked) {
                        button.classList.add('bookmarked');
                        button.classList.remove('btn-outline-secondary');
                        button.classList.add('btn-warning');
                        if (icon) {
                            icon.classList.remove('fa-regular');
                            icon.classList.add('fa-solid');
                        }
                    } else {
                        button.classList.remove('bookmarked');
                        button.classList.remove('btn-warning');
                        button.classList.add('btn-outline-secondary');
                        if (icon) {
                            icon.classList.remove('fa-solid');
                            icon.classList.add('fa-regular');
                        }
                    }
                    showToast(data.message || 'Saved status updated!');
                }
            } catch (err) {
                console.error('Error toggling bookmark:', err);
            }
        });
    });

    // Auto-dismiss alert messages after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            if (bsAlert) bsAlert.close();
        });
    }, 5000);
});

// Toast Notification Helper
function showToast(message) {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1100';
        document.body.appendChild(toastContainer);
    }

    const toastEl = document.createElement('div');
    toastEl.className = 'toast align-items-center text-white bg-dark border-0 shadow';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fa-solid fa-circle-check text-success me-2"></i> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
    bsToast.show();

    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}
