    if (document.getElementById("file_input")) {    
        const fileInput = document.getElementById('file_input');
        const preview = document.getElementById('picture_preview');
        const fileName = document.getElementById('picture_file_name');
        const dropZone = document.getElementById('picture_drop_zone');
        let previewUrl = null;

        function updatePreview() {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
            previewUrl = null;
            preview.hidden = true;
            preview.removeAttribute('src');
            fileInput.setCustomValidity('');
            const file = fileInput.files[0];
            if (!file) {
                fileName.textContent = '선택한 파일이 없습니다.';
                return;
            }
            if (!/\.(png|jpe?g|gif|webp)$/i.test(file.name)) {
                fileInput.setCustomValidity('PNG, JPG, GIF, WEBP 사진 파일을 선택해 주세요.');
                fileName.textContent = '사진 파일 형식을 확인해 주세요.';
                fileInput.reportValidity();
                return;
            }
            fileName.textContent = file.name;
            previewUrl = URL.createObjectURL(file);
            preview.src = previewUrl;
            preview.hidden = false;
        }

        fileInput.addEventListener('change', updatePreview);
        dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });
        dropZone.addEventListener('drop', (event) => {
            event.preventDefault();
            dropZone.classList.remove('drag-over');
            const file = event.dataTransfer.files[0];
            if (!file) return;
            const transfer = new DataTransfer();
            transfer.items.add(file);
            fileInput.files = transfer.files;
            updatePreview();
        });
    }