// Load counselors when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadCounselors();
});

function loadCounselors() {
    fetch('/counselors')
        .then(response => response.json())
        .then(counselors => {
            const select = document.getElementById('counselor-select');
            window.__counselors = counselors;
            for (const [name, details] of Object.entries(counselors)) {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${name} - ${details.specialty || ''}`;
                select.appendChild(option);
            }
            select.addEventListener('change', () => {
                const name = select.value;
                const note = document.getElementById('counselor-days-note');
                if (name && counselors[name]) {
                    const days = counselors[name].available_days || [];
                    note.textContent = days.length ? `Available days: ${days.join(', ')}` : '';
                } else {
                    note.textContent = '';
                }
            });
        });
}

function checkAvailability() {
    const counselor = document.getElementById('counselor-select').value;
    const date = document.getElementById('appointment-date').value;
    
    if (!counselor || !date) {
        addMessage('Please select both a counselor and date.', 'bot');
        return;
    }
    
    // Validate weekday based on counselor availability to avoid empty queries
    const days = (window.__counselors && window.__counselors[counselor] && window.__counselors[counselor].available_days) || [];
    if (days.length) {
        const dayName = new Date(date).toLocaleDateString('en-US', { weekday: 'long' });
        if (!days.includes(dayName)) {
            // Suggest the next valid day
            const nextDate = nextDateForDay(days);
            addMessage(`Selected date is a ${dayName}, but ${counselor} works on ${days.join(', ')}. Suggesting ${nextDate} instead.`, 'bot');
        }
    }

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            intent: 'check_availability',
            counselor: counselor,
            date: date
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addMessage(data.error, 'bot');
            return;
        }
        
        const slotsDiv = document.getElementById('available-slots');
        slotsDiv.innerHTML = '';
        
        if (data.slots.length === 0) {
            addMessage(`No available slots for ${counselor} on ${date}`, 'bot');
            return;
        }
        
        data.slots.forEach(slot => {
            const button = document.createElement('button');
            button.classList.add('slot-button');
            button.textContent = slot.split(' ')[1]; // Show only time
            button.onclick = () => bookAppointment(counselor, slot);
            slotsDiv.appendChild(button);
        });
        
        addMessage(`Available slots for ${counselor} on ${date}. Please select a time from the sidebar.`, 'bot');
    });
}

function nextDateForDay(days) {
    const map = { Sunday:0, Monday:1, Tuesday:2, Wednesday:3, Thursday:4, Friday:5, Saturday:6 };
    const today = new Date();
    for (let i=1; i<=14; i++) {
        const d = new Date(today);
        d.setDate(today.getDate() + i);
        const name = d.toLocaleDateString('en-US', { weekday: 'long' });
        if (days.includes(name)) {
            return d.toISOString().slice(0,10);
        }
    }
    return '';
}

function bookAppointment(counselor, slot) {
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            intent: 'book_appointment',
            counselor: counselor,
            slot: slot,
            student_id: 'demo-user' // In a real app, this would be the authenticated user's ID
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addMessage(data.error, 'bot');
            return;
        }
        
        const confirmation = data.appointment;
        addMessage(`Appointment confirmed with ${confirmation.counselor} at ${confirmation.appointment_time}. Your confirmation code is: ${confirmation.confirmation_code}`, 'bot');
        
        // Clear the available slots
        document.getElementById('available-slots').innerHTML = '';
    });
}

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    
    if (message === '') return;
    
    // Add user message to chat
    addMessage(message, 'user');
    userInput.value = '';

    // Send message to server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({ 
            message: message,
            user_id: 'default'  // Add a default user ID
        })
    })
    .then(async response => {
        let data;
        try { data = await response.json(); } catch (e) { data = { error: 'Invalid server response' }; }
        if (!response.ok || data.error) {
            addMessage(data.error || 'Sorry, there was an error processing your message.', 'bot');
            return;
        }
        addMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Sorry, there was an error processing your message.', 'bot');
    });
}

function addMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Allow sending message with Enter key
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});