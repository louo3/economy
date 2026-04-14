async function triggerScan() {
    const btn = document.querySelector('.btn-primary');
    const idleStatus = document.getElementById('idle-status');
    const scanStatus = document.getElementById('scan-status');
    
    // UI Feedback
    btn.disabled = true;
    idleStatus.style.display = 'none';
    scanStatus.style.display = 'flex';

    try {
        const response = await fetch('/scan/now', {
            method: 'POST'
        });
        const result = await response.json();
        
        // Since it's a background task, we'll just alert the user
        alert('掃描已在後台啟動，完成後將自動發送通知。請在幾分鐘後重新整理頁面查看結果。');
        
        // Reset UI after a delay
        setTimeout(() => {
            btn.disabled = false;
            idleStatus.style.display = 'block';
            scanStatus.style.display = 'none';
        }, 5000);

    } catch (error) {
        console.error('Error:', error);
        alert('啟動掃描失敗，請檢查系統日誌。');
        btn.disabled = false;
        idleStatus.style.display = 'block';
        scanStatus.style.display = 'none';
    }
}

// Table Sorting Logic
document.addEventListener('DOMContentLoaded', () => {
    const table = document.getElementById('main-table');
    if (!table) return;

    const headers = table.querySelectorAll('th.sortable');
    const tbody = table.querySelector('tbody');

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const type = header.getAttribute('data-type');
            const index = Array.from(header.parentNode.children).indexOf(header);
            const isAsc = header.classList.contains('sort-asc');
            
            // Remove existing sort classes
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            
            // Toggle sort direction
            const direction = isAsc ? 'desc' : 'asc';
            header.classList.add(`sort-${direction}`);

            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Handle if there's no data (the "尚未有掃描紀錄" row)
            if (rows.length === 1 && rows[0].cells.length === 1) return;

            rows.sort((a, b) => {
                let cellA = a.cells[index].innerText.trim();
                let cellB = b.cells[index].innerText.trim();

                if (type === 'number') {
                    cellA = parseFloat(cellA) || 0;
                    cellB = parseFloat(cellB) || 0;
                } else if (type === 'date') {
                    cellA = new Date(cellA).getTime() || 0;
                    cellB = new Date(cellB).getTime() || 0;
                }

                if (cellA < cellB) return direction === 'asc' ? -1 : 1;
                if (cellA > cellB) return direction === 'asc' ? 1 : -1;
                return 0;
            });

            // Append sorted rows back to tbody
            rows.forEach(row => tbody.appendChild(row));
        });
    });

    // Set default indicator for Pullback Date (which is sorted by backend)
    // Pullback Date is index 4
    const pullbackHeader = headers[4];
    if (pullbackHeader) pullbackHeader.classList.add('sort-desc');
});
