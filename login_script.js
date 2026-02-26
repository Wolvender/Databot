// login_script.js - Handles "Remember Me" functionality using LocalStorage
(function() {
    // 1. CHECK FOR SAVED CREDENTIALS ON LOAD
    const saved = localStorage.getItem('databot_creds');
    if (!saved) return;

    let creds;
    try {
        creds = JSON.parse(atob(saved));
    } catch (e) {
        console.error("Invalid saved credentials");
        return;
    }

    // Helper: Set value on React/Streamlit inputs correctly
    function setNativeValue(element, value) {
        const valueSetter = Object.getOwnPropertyDescriptor(element, 'value').set;
        const prototype = Object.getPrototypeOf(element);
        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
        
        if (valueSetter && valueSetter !== prototypeValueSetter) {
            prototypeValueSetter.call(element, value);
        } else {
            valueSetter.call(element, value);
        }
        element.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Main function to fill the form
    function fillCredentials() {
        const userParams = ['Username', 'User', 'Email'];
        const passParams = ['Password', 'Pass'];
        
        const doc = parent.document;
        
        // Find Username field
        let userInput = null;
        for (let label of userParams) {
            userInput = doc.querySelector(`input[aria-label="${label}"]`);
            if (userInput) break;
        }
        
        // Find Password field
        let passInput = null;
        for (let label of passParams) {
            passInput = doc.querySelector(`input[aria-label="${label}"]`);
            if (passInput) break;
        }

        // Fill Username
        if (userInput && creds.u && !userInput.value) {
            setNativeValue(userInput, creds.u);
        }

        // Fill Password
        if (passInput && creds.p && !passInput.value) {
            setNativeValue(passInput, creds.p);
        }
        
        // Check "Remember me" box if it isn't already
        const checkbox = doc.querySelector('input[type="checkbox"]');
        if (checkbox && !checkbox.checked) {
            checkbox.click();
        }
    }

    // 2. WATCH FOR THE FORM TO APPEAR (MutationObserver)
    const observer = new MutationObserver((mutations) => {
        fillCredentials();
    });

    observer.observe(parent.document.body, { childList: true, subtree: true });
    
    // Try once immediately
    fillCredentials();
})();

// 3. LISTEN FOR SAVE/CLEAR MESSAGES FROM PYTHON
window.addEventListener('message', function(e) {
    if (e.data.type === 'save_creds') {
        // Save: Encode and store in localStorage
        const payload = btoa(JSON.stringify({u: e.data.u, p: e.data.p}));
        localStorage.setItem('databot_creds', payload);
    } else if (e.data.type === 'clear_creds') {
        // Clear: Remove from localStorage
        localStorage.removeItem('databot_creds');
    }
});
