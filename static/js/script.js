document.addEventListener('DOMContentLoaded', () => {
    // Check if user is authenticated
    checkAuthStatus();
    
    // Set default dates
    const today = new Date();
    const twoWeeksLater = new Date();
    twoWeeksLater.setDate(today.getDate() + 14);
    
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    
    if (startDateInput && endDateInput) {
        startDateInput.valueAsDate = today;
        endDateInput.valueAsDate = twoWeeksLater;
    }
    
    // Event listeners
    const addLinkButton = document.getElementById('add-link');
    if (addLinkButton) {
        addLinkButton.addEventListener('click', addCalendlyLink);
    }
    
    const findSlotsButton = document.getElementById('find-slots');
    if (findSlotsButton) {
        findSlotsButton.addEventListener('click', findAvailableSlots);
    }
    
    // Setup initial remove buttons
    document.querySelectorAll('.remove').forEach(button => {
        button.addEventListener('click', function() {
            const inputs = document.querySelectorAll('.calendly-link');
            if (inputs.length > 1) {
                this.parentElement.remove();
            } else {
                document.getElementById('error').textContent = 'You need at least one Calendly link.';
                setTimeout(() => {
                    document.getElementById('error').textContent = '';
                }, 3000);
            }
        });
    });
});

function checkAuthStatus() {
    // This would normally check if the user has a valid session
    // For this demo, we'll just show the app section
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code') || document.cookie.includes('session')) {
        document.getElementById('auth-section').style.display = 'none';
        document.getElementById('app-section').style.display = 'block';
    }
}

function addCalendlyLink() {
    const inputsContainer = document.getElementById('calendly-inputs');
    const newLink = document.createElement('div');
    newLink.className = 'calendly-link';
    newLink.innerHTML = `
        <input type="text" placeholder="Enter Calendly link (e.g., https://calendly.com/username/30min)" class="link-input">
        <button class="remove">Remove</button>
    `;
    
    newLink.querySelector('.remove').addEventListener('click', function() {
        const inputs = document.querySelectorAll('.calendly-link');
        if (inputs.length > 1) {
            this.parentElement.remove();
        } else {
            document.getElementById('error').textContent = 'You need at least one Calendly link.';
            setTimeout(() => {
                document.getElementById('error').textContent = '';
            }, 3000);
        }
    });
    
    inputsContainer.appendChild(newLink);
}

async function findAvailableSlots() {
    const statusDiv = document.getElementById('status');
    const errorDiv = document.getElementById('error');
    const resultsDiv = document.getElementById('results');
    
    // Clear previous results
    statusDiv.textContent = 'Searching for available slots...';
    errorDiv.textContent = '';
    resultsDiv.innerHTML = '';
    
    // Get inputs
    const linkInputs = document.querySelectorAll('.link-input');
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    // Validate inputs
    const calendlyLinks = [];
    for (const input of linkInputs) {
        if (input.value.trim() === '') {
            errorDiv.textContent = 'Please fill in all Calendly links.';
            statusDiv.textContent = '';
            return;
        }
        calendlyLinks.push(input.value.trim());
    }
    
    if (!startDate || !endDate) {
        errorDiv.textContent = 'Please select both start and end dates.';
        statusDiv.textContent = '';
        return;
    }
    
    if (new Date(startDate) > new Date(endDate)) {
        errorDiv.textContent = 'End date must be after start date.';
        statusDiv.textContent = '';
        return;
    }
    
    try {
        // Call our backend API
        const response = await fetch('/api/check-availability', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                links: calendlyLinks,
                startDate: startDate,
                endDate: endDate
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${await response.text()}`);
        }
        
        const availableSlots = await response.json();
        
        if (Object.keys(availableSlots).length === 0) {
            statusDiv.textContent = 'No common available slots found in the selected date range.';
            return;
        }
        
        // Display results
        statusDiv.textContent = 'Available slots found!';
        
        // Sort dates
        const sortedDates = Object.keys(availableSlots).sort();
        
        for (const date of sortedDates) {
            const dateSlots = document.createElement('div');
            dateSlots.className = 'date-slots';
            
            const dateHeader = document.createElement('div');
            dateHeader.className = 'date-header';
            dateHeader.textContent = formatDate(date);
            dateSlots.appendChild(dateHeader);
            
            const timeSlots = document.createElement('div');
            timeSlots.className = 'time-slots';
            
            availableSlots[date].forEach(slot => {
                const timeSlot = document.createElement('div');
                timeSlot.className = 'time-slot';
                timeSlot.textContent = formatTime(slot);
                timeSlots.appendChild(timeSlot);
            });
            
            dateSlots.appendChild(timeSlots);
            resultsDiv.appendChild(dateSlots);
        }
    } catch (error) {
        errorDiv.textContent = `Error: ${error.message}`;
        statusDiv.textContent = '';
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString(undefined, options);
}

function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}