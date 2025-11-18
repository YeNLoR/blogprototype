const editButtons = document.querySelectorAll(".toggle-edit-button");

editButtons.forEach(button => {
    button.addEventListener('click', (e) => {
        const targetSelector = button.getAttribute('data-target');
        const targetContentSelector = button.getAttribute('data-content-target')
        const editContainer = document.querySelector(targetSelector);
        const contentContainer = document.querySelector(targetContentSelector)

        if (editContainer) {
            editContainer.style.display = 'block';
            contentContainer.style.display = 'none';
        }
    });
});

const cancelButtons = document.querySelectorAll(".edit-comment-cancel");

cancelButtons.forEach(button => {
    button.addEventListener('click', (e) => {
        const editContainer = button.closest('.edit-comment');

        const parentRow = editContainer.closest('.row');

        const contentContainer = parentRow.querySelector('.comment-content-display');

        if (editContainer) {
            editContainer.style.display = 'none';
        }

        if (contentContainer) {
            contentContainer.style.display = 'block';
        }
    });
});

