// CDP-based background service worker for network interception
console.log('IntenseRP CDP Network Interceptor background service worker loaded');

let isIntercepting = false;
let activeTabId = null;
let targetRequestId = null;
let streamBuffer = [];
const localApiUrl = 'http://127.0.0.1:5000';

// Debug helper to send logs to IntenseRP console
function debugLog(message) {
  console.log(message); // Keep browser console too
  fetch(`${localApiUrl}/network/debug-log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message })
  }).catch(() => {}); // Silent fail if API not available
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'startInterception') {
    debugLog('🔵 Starting CDP network interception...');
    startCDPInterception(sender.tab.id);
    sendResponse({ status: 'started' });
  } else if (message.action === 'stopInterception') {
    debugLog('🔴 Stopping CDP network interception...');
    stopCDPInterception();
    sendResponse({ status: 'stopped' });
  }
});

// Start CDP interception
async function startCDPInterception(tabId) {
  if (isIntercepting) return;
  
  try {
    activeTabId = tabId;
    
    // Attach debugger to the tab
    await new Promise((resolve, reject) => {
      debugLog(`Attempting CDP attach to tab: ${tabId}`);
      chrome.debugger.attach({ tabId: tabId }, '1.3', () => {
        if (chrome.runtime.lastError) {
          debugLog(`❌ CDP attach failed: ${chrome.runtime.lastError.message}`);
          reject(chrome.runtime.lastError);
        } else {
          debugLog(`✅ CDP debugger attached to tab: ${tabId}`);
          resolve();
        }
      });
    });
    
    // Enable Network domain
    await sendCDPCommand(tabId, 'Network.enable');
    console.log('✅ CDP Network domain enabled');
    
    // Enable Runtime domain for better error handling
    await sendCDPCommand(tabId, 'Runtime.enable');
    
    isIntercepting = true;
    
    // Set up event listeners
    chrome.debugger.onEvent.addListener(onCDPEvent);
    
    console.log('🟢 CDP network interception started');
    
  } catch (error) {
    console.error('❌ Error starting CDP interception:', error);
    isIntercepting = false;
  }
}

// Stop CDP interception
async function stopCDPInterception() {
  if (!isIntercepting || !activeTabId) return;
  
  try {
    // Remove event listeners
    chrome.debugger.onEvent.removeListener(onCDPEvent);
    
    // Detach debugger
    chrome.debugger.detach({ tabId: activeTabId });
    console.log('✅ CDP debugger detached from tab:', activeTabId);
    
    isIntercepting = false;
    activeTabId = null;
    targetRequestId = null;
    streamBuffer = [];
    
    console.log('🔴 CDP network interception stopped');
    
  } catch (error) {
    console.error('❌ Error stopping CDP interception:', error);
  }
}

// Send CDP command
function sendCDPCommand(tabId, method, params = {}) {
  return new Promise((resolve, reject) => {
    chrome.debugger.sendCommand({ tabId: tabId }, method, params, (result) => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(result);
      }
    });
  });
}

// Handle CDP events
function onCDPEvent(source, method, params) {
  if (!isIntercepting || source.tabId !== activeTabId) return;
  
  try {
    switch (method) {
      case 'Network.requestWillBeSent':
        handleRequestWillBeSent(params);
        break;
      case 'Network.responseReceived':
        handleResponseReceived(params);
        break;
      case 'Network.dataReceived':
        handleDataReceived(params);
        break;
      case 'Network.eventSourceMessageReceived':
        handleEventSourceMessage(params);
        break;
      case 'Network.loadingFinished':
        handleLoadingFinished(params);
        break;
      case 'Network.loadingFailed':
        handleLoadingFailed(params);
        break;
    }
  } catch (error) {
    console.error('❌ Error handling CDP event:', error);
  }
}

// Handle request will be sent
function handleRequestWillBeSent(params) {
  const url = params.request.url;
  
  debugLog(`📤 Request: ${params.requestId} - ${url} (current target: ${targetRequestId})`);
  
  // ONLY track the actual streaming endpoint, ignore all other DeepSeek API calls
  if (url.includes('/api/v0/chat/completion')) {
    debugLog(`🟡 REAL DeepSeek STREAMING request detected - SETTING TARGET: ${params.requestId}`);
    targetRequestId = params.requestId;
    
    // Notify local API about request
    fetch(`${localApiUrl}/network/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        requestId: params.requestId,
        url: url,
        method: params.request.method,
        timestamp: Date.now()
      })
    }).catch(err => {
      debugLog(`❌ Failed to send request notification: ${err}`);
    });
  }
}

// Handle response received
function handleResponseReceived(params) {
  if (params.requestId !== targetRequestId) return;
  
  const response = params.response;
  const contentType = response.headers['content-type'] || response.headers['Content-Type'] || '';
  
  console.log('🟡 Response received for DeepSeek API:', {
    status: response.status,
    contentType: contentType,
    requestId: params.requestId
  });
  
  // Check if it's a streaming response
  if (contentType.includes('text/event-stream') || contentType.includes('text/plain')) {
    console.log('🟢 Streaming response detected');
    
    // Reset stream buffer
    streamBuffer = [];
    
    // Notify local API about response start
    fetch(`${localApiUrl}/network/response-start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        requestId: params.requestId,
        responseHeaders: response.headers,
        timestamp: Date.now()
      })
    }).catch(err => {
      console.error('Failed to send response start notification:', err);
    });
  }
}

let lastProcessedData = '';
let dataProcessingQueue = [];
let isProcessingQueue = false;

// Handle data received
async function handleDataReceived(params) {
  if (params.requestId !== targetRequestId) return;
  
  debugLog(`🟢 Data received for target request: ${params.requestId}, dataLength: ${params.dataLength}`);
  
  // Add to processing queue instead of processing immediately
  dataProcessingQueue.push(params);
  
  // Process queue if not already processing
  if (!isProcessingQueue) {
    processDataQueue();
  }
}

// Process data queue sequentially to maintain order
async function processDataQueue() {
  if (isProcessingQueue) return;
  isProcessingQueue = true;
  
  while (dataProcessingQueue.length > 0) {
    const params = dataProcessingQueue.shift();
    
    try {
      // Wait longer before processing to let data stabilize
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Get the actual response body data
      const responseBody = await sendCDPCommand(activeTabId, 'Network.getResponseBody', {
        requestId: params.requestId
      });
      
      if (responseBody && responseBody.body) {
        const data = responseBody.base64Encoded ? 
          atob(responseBody.body) : responseBody.body;
        
        // Only process new data (incremental)
        if (data.length > lastProcessedData.length && data.startsWith(lastProcessedData)) {
          const newData = data.substring(lastProcessedData.length);
          if (newData.trim()) {
            debugLog(`🟢 New incremental data (${newData.length} chars): ${newData.substring(0, 50)}...`);
            
            // Process each SSE line individually with delays
            await processSSEDataSlowly(newData);
          }
          lastProcessedData = data;
        }
      }
      
    } catch (error) {
      debugLog(`❌ Error getting response body: ${error.message}`);
    }
    
    // Longer delay between queue items
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  
  isProcessingQueue = false;
}

// Process SSE data slowly and carefully
async function processSSEDataSlowly(data) {
  const lines = data.split('\n');
  
  for (const line of lines) {
    if (line.trim()) {
      if (line.startsWith('data: ')) {
        const eventData = line.substring(6);
        debugLog(`📝 Processing SSE Data: ${eventData.substring(0, 50)}...`);
        
        // Send each data item individually with delay
        await fetch(`${localApiUrl}/network/stream-data`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            data: eventData,
            timestamp: Date.now()
          })
        }).catch(err => {
          debugLog(`❌ Failed to forward stream data: ${err}`);
        });
        
        // Small delay between data items
        await new Promise(resolve => setTimeout(resolve, 20));
        
      } else if (line.startsWith('event: ')) {
        const eventType = line.substring(7);
        debugLog(`🎯 Processing SSE Event: ${eventType}`);
        
        await fetch(`${localApiUrl}/network/stream-event`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            event: eventType,
            timestamp: Date.now()
          })
        }).catch(err => {
          debugLog(`❌ Failed to forward stream event: ${err}`);
        });
      }
    }
  }
}

// Handle loading finished
function handleLoadingFinished(params) {
  debugLog(`📥 Loading finished: ${params.requestId} (target: ${targetRequestId})`);
  
  if (params.requestId !== targetRequestId) {
    debugLog(`⚠️ Ignoring loadingFinished for non-target request ${params.requestId}`);
    return;
  }
  
  debugLog('🟢 Loading finished for DeepSeek API request - MARKING COMPLETE');
  
  // Notify local API about response end
  fetch(`${localApiUrl}/network/response-end`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      requestId: params.requestId,
      timestamp: Date.now()
    })
  }).catch(err => {
    debugLog(`❌ Failed to send response end notification: ${err}`);
  });
  
  // Reset for next request
  targetRequestId = null;
  streamBuffer = [];
}

// Handle loading failed
function handleLoadingFailed(params) {
  if (params.requestId !== targetRequestId) return;
  
  console.log('🔴 Loading failed for DeepSeek API request:', params.errorText);
  
  // Notify local API about error
  fetch(`${localApiUrl}/network/response-error`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      requestId: params.requestId,
      error: params.errorText,
      timestamp: Date.now()
    })
  }).catch(err => {
    console.error('Failed to send error notification:', err);
  });
  
  // Reset for next request
  targetRequestId = null;
  streamBuffer = [];
}

// Handle EventSource messages (the proper way!)
function handleEventSourceMessage(params) {
  console.log('🟢 EventSource message received:', params);
  
  // Forward the SSE data directly to local API
  fetch(`${localApiUrl}/network/stream-data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: params.data,
      eventName: params.eventName || 'message',
      eventId: params.eventId,
      timestamp: params.timestamp
    })
  }).catch(err => {
    console.error('Failed to forward EventSource data:', err);
  });
}

// Parse and forward streaming data
function parseAndForwardStreamData(data) {
  debugLog(`🔄 Parsing streaming data: ${data.substring(0, 200)}...`);
  
  // Split by newlines to handle SSE format
  const lines = data.split('\n');
  
  for (const line of lines) {
    if (line.trim()) {
      if (line.startsWith('data: ')) {
        const eventData = line.substring(6); // Remove 'data: ' prefix
        debugLog(`📝 SSE Data: ${eventData.substring(0, 100)}...`);
        
        // Forward to local API
        fetch(`${localApiUrl}/network/stream-data`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            data: eventData,
            timestamp: Date.now()
          })
        }).catch(err => {
          debugLog(`❌ Failed to forward stream data: ${err}`);
        });
        
      } else if (line.startsWith('event: ')) {
        const eventType = line.substring(7); // Remove 'event: ' prefix
        debugLog(`🎯 SSE Event: ${eventType}`);
        
        // Forward to local API
        fetch(`${localApiUrl}/network/stream-event`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            event: eventType,
            timestamp: Date.now()
          })
        }).catch(err => {
          debugLog(`❌ Failed to forward stream event: ${err}`);
        });
      }
    }
  }
}

// Handle debugger detach (cleanup)
chrome.debugger.onDetach.addListener((source, reason) => {
  if (source.tabId === activeTabId) {
    debugLog(`🔴 Debugger detached from tab: ${source.tabId}, Reason: ${reason}`);
    isIntercepting = false;
    activeTabId = null;
    targetRequestId = null;
    streamBuffer = [];
  }
});

console.log('CDP Network Interceptor background script initialized');