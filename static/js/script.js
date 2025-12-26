document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('url-input');
    const extractBtn = document.getElementById('extract-btn');
    const resultsSection = document.getElementById('results-section');
    const loader = document.getElementById('loader');
    const emptyState = document.getElementById('empty-state');
    const filtersSummary = document.getElementById('filters-summary');
    const totalCountSpan = document.getElementById('total-count');
    const selectAllBtn = document.getElementById('select-all-btn');
    const downloadAllBtn = document.getElementById('download-all-btn');
    const themeToggle = document.getElementById('theme-toggle');

    let allImages = []; // Stores objects { url, element }

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        themeToggle.innerHTML = newTheme === 'dark' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    });

    // Extract Function
    extractBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) return;

        // Reset UI
        resultsSection.innerHTML = '';
        resultsSection.classList.add('hidden');
        filtersSummary.classList.add('hidden');
        emptyState.classList.add('hidden');
        loader.classList.remove('hidden');
        allImages = [];

        try {
            const response = await fetch('/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await response.json();

            if (data.success && data.images.length > 0) {
                renderImages(data.images);
            } else {
                emptyState.classList.remove('hidden');
            }
        } catch (error) {
            console.error(error);
            emptyState.querySelector('h3').textContent = 'Error';
            emptyState.querySelector('p').textContent = 'Failed to fetch images. Please check the URL.';
            emptyState.classList.remove('hidden');
        } finally {
            loader.classList.add('hidden');
        }
    });

    function renderImages(imagesData) {
        totalCountSpan.textContent = imagesData.length;
        filtersSummary.classList.remove('hidden');
        resultsSection.classList.remove('hidden');

        imagesData.forEach((imgData, index) => {
            const card = document.createElement('div');
            card.className = 'image-card selected'; // Default selected
            
            // Proxy logic could be added here if direct loading fails, 
            // but for now we try direct URL first.
            const proxyUrl = `/proxy-image?url=${encodeURIComponent(imgData.url)}`;

            card.innerHTML = `
                <div class="image-wrapper">
                    <div class="select-check"><i class="fa-solid fa-check"></i></div>
                    <img src="${proxyUrl}" loading="lazy" alt="Extracted Image">
                    
                    <div class="card-actions">
                        <a href="${proxyUrl}" download target="_blank" class="action-btn" title="Download">
                            <i class="fa-solid fa-download"></i>
                        </a>
                    </div>
                </div>
            `;

            // Selection Logic
            card.querySelector('.select-check').addEventListener('click', (e) => {
                e.stopPropagation();
                card.classList.toggle('selected');
                updateDownloadButton();
            });
            
            // Also toggle on wrapper click (optional UX)
            card.querySelector('.image-wrapper').addEventListener('click', (e) => {
                if(e.target.tagName !== 'A' && e.target.tagName !== 'I') {
                    card.classList.toggle('selected');
                    updateDownloadButton();
                }
            });

            resultsSection.appendChild(card);
            allImages.push({ url: imgData.url, element: card });
        });
        
        updateDownloadButton();
    }

    // Select All / Deselect All
    let allSelected = true;
    selectAllBtn.addEventListener('click', () => {
        allSelected = !allSelected;
        allImages.forEach(imgObj => {
            if (allSelected) imgObj.element.classList.add('selected');
            else imgObj.element.classList.remove('selected');
        });
        selectAllBtn.textContent = allSelected ? 'Deselect All' : 'Select All';
        updateDownloadButton();
    });

    function updateDownloadButton() {
        const selectedCount = allImages.filter(i => i.element.classList.contains('selected')).length;
        downloadAllBtn.innerHTML = `<i class="fa-solid fa-download"></i> Download Selected (${selectedCount})`;
        downloadAllBtn.disabled = selectedCount === 0;
        if(selectedCount === 0) downloadAllBtn.style.opacity = '0.5';
        else downloadAllBtn.style.opacity = '1';
    }

    // Download ZIP
    downloadAllBtn.addEventListener('click', async () => {
        const selectedUrls = allImages
            .filter(i => i.element.classList.contains('selected'))
            .map(i => i.url);

        if (selectedUrls.length === 0) return;

        const originalText = downloadAllBtn.innerHTML;
        downloadAllBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Zipping...`;
        downloadAllBtn.disabled = true;

        try {
            const response = await fetch('/download-zip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ images: selectedUrls })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'extracted_images.zip';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            } else {
                alert('Failed to create ZIP');
            }
        } catch (e) {
            console.error(e);
            alert('Error downloading images');
        } finally {
            downloadAllBtn.innerHTML = originalText;
            downloadAllBtn.disabled = false;
        }
    });
});
