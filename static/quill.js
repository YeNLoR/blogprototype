const quill = new Quill("#editor", {
    modules: {
        toolbar: {
            container: [
                [{ header: [1, 2, 3, 4, 5, 6, false] }],
                ['bold', 'italic', 'underline', 'strike'],
                ['link', 'image', 'video'],
                ['code-block', 'blockquote']
            ],
            handlers: {
                image: imageHandler
            }
        },
    },
    theme: "snow",
});

function imageHandler() {
    const tooltip = this.quill.theme.tooltip;
    const originalSave = tooltip.save;
    tooltip.save = () => {
        const range = this.quill.getSelection(true);
        const value = tooltip.textbox.value;

        if (value) {
            this.quill.insertEmbed(range.index, 'image', value, Quill.sources.USER);
        }

        tooltip.save = originalSave;
        tooltip.hide();
    };
    tooltip.edit('image');
    tooltip.textbox.placeholder = 'Embed URL';
}

document.getElementById('post_form').addEventListener('submit', (e) => {
    document.getElementById('content').value = quill.root.innerHTML;
});