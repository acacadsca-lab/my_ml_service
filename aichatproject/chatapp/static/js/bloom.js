// Bloom Animation Logic
let typingTimer;
const BLOOM_DELAY = 150; // Time before flower wilts after stopping typing
let isTyping = false;

function initBloomAnimation() {
    const textarea = document.getElementById('blogContent');
    const flower = document.getElementById('bloomFlower');
    const hint = document.getElementById('bloomHint');
    const wordCountEl = document.getElementById('wordCount');
    
    if (!textarea || !flower) return;
    
    // Track typing
    textarea.addEventListener('input', function() {
        // Update word count
        const words = this.value.trim().split(/\s+/).filter(word => word.length > 0);
        wordCountEl.textContent = words.length;
        
        // Bloom the flower
        if (!isTyping) {
            bloom();
        }
        
        isTyping = true;
        
        // Reset the timer
        clearTimeout(typingTimer);
        
        // Set timer to wilt when typing stops
        typingTimer = setTimeout(function() {
            wilt();
            isTyping = false;
        }, BLOOM_DELAY);
    });
    
    // Keyboard events for immediate response
    textarea.addEventListener('keydown', function(e) {
        // Bloom on any key press (except special keys)
        if (!e.ctrlKey && !e.metaKey && !e.altKey && e.key.length === 1) {
            if (!isTyping) {
                bloom();
            }
        }
    });
    
    function bloom() {
        flower.classList.add('blooming');
        hint.classList.add('hidden');
        
        // Add extra animation effects
        flower.style.transform = 'scale(1.05)';
        setTimeout(() => {
            flower.style.transform = 'scale(1)';
        }, 200);
    }
    
    function wilt() {
        flower.classList.remove('blooming');
        hint.classList.remove('hidden');
    }
    
    // Focus effect
    textarea.addEventListener('focus', function() {
        document.querySelector('.textarea-wrapper').style.boxShadow = 
            '0 0 0 3px rgba(255, 181, 194, 0.3)';
    });
    
    textarea.addEventListener('blur', function() {
        document.querySelector('.textarea-wrapper').style.boxShadow = 'none';
        
        // Wilt when focus is lost
        wilt();
        isTyping = false;
        clearTimeout(typingTimer);
    });
}

// Auto-hide messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Add typing effect to hero title (optional enhancement)
function typeWriter(element, text, speed = 50) {
    let i = 0;
    element.textContent = '';
    
    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}