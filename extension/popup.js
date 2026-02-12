document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('downloadBtn');
    const input = document.getElementById('algoName');
    const status = document.getElementById('status');

    btn.addEventListener('click', async () => {
        const algoName = input.value.trim();
        if (!algoName) {
            status.textContent = "Please enter a name.";
            status.style.color = "red";
            return;
        }

        status.textContent = "Processing...";
        status.style.color = "blue";

        try {
            // Get current tab URL
            const [tab] = await browser.tabs.query({ active: true, currentWindow: true });

            if (!tab.url.includes("arxiv.org")) {
                status.textContent = "Not an ArXiv page.";
                status.style.color = "red";
                return;
            }

            // Send to Local Backend
            const response = await fetch('http://localhost:8000/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: tab.url,
                    algo_name: algoName
                })
            });

            const data = await response.json();

            if (response.ok) {
                status.textContent = `Saved to /${algoName}`;
                status.style.color = "green";
                setTimeout(() => window.close(), 1500);
            } else {
                throw new Error(data.detail || "Server error");
            }

        } catch (error) {
            status.textContent = "Error: " + error.message;
            status.style.color = "red";
            console.error(error);
        }
    });

    // Allow Enter key to submit
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') btn.click();
    });
});