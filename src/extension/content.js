// Content script for CDP-based network interception
console.log('IntenseRP CDP Network Interceptor content script loaded');

let isIntercepting = false;

// Functions to control interception
function startInterception() {
  if (isIntercepting) return;
  
  console.log('🔵 Starting CDP network interception...');
  isIntercepting = true;
  
  // Send message to background script to start CDP interception
  chrome.runtime.sendMessage({ action: 'startInterception' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('❌ Error starting CDP interception:', chrome.runtime.lastError);
      isIntercepting = false;
    } else {
      console.log('✅ CDP interception started:', response);
    }
  });
}

function stopInterception() {
  if (!isIntercepting) return;
  
  console.log('🔴 Stopping CDP network interception...');
  isIntercepting = false;
  
  // Send message to background script to stop CDP interception
  chrome.runtime.sendMessage({ action: 'stopInterception' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('❌ Error stopping CDP interception:', chrome.runtime.lastError);
    } else {
      console.log('✅ CDP interception stopped:', response);
    }
  });
}

// Listen for messages from our API
window.addEventListener('message', (event) => {
  // Only accept messages from same origin
  if (event.origin !== 'https://chat.deepseek.com') return;
  
  if (event.data.action === 'startNetworkInterception') {
    startInterception();
  } else if (event.data.action === 'stopNetworkInterception') {
    stopInterception();
  }
});

// Handle page unload
window.addEventListener('beforeunload', () => {
  if (isIntercepting) {
    stopInterception();
  }
});

// Handle visibility change
document.addEventListener('visibilitychange', () => {
  if (document.hidden && isIntercepting) {
    // Page is hidden, but keep interception active
    console.log('🟡 Page hidden, keeping CDP interception active');
  } else if (!document.hidden && !isIntercepting) {
    // Page is visible again, check if we should restart
    console.log('🟡 Page visible, CDP interception status:', isIntercepting);
  }
});

console.log('IntenseRP CDP content script initialized');