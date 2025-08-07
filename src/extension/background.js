// CDP-based background service worker for network interception
console.log('IntenseRP CDP Network Interceptor background service worker loaded');

let isIntercepting = false;
let activeTabId = null;
let targetRequestId = null;
let streamBuffer = [];
let completionTriggered = false;
const DEFAULT_PORT = 5000;
const localApiUrl = `http://127.0.0.1:${DEFAULT_PORT}`;

// Debug helper to send logs to IntenseRP console
function debugLog(message) {
  // console.log(message); // Keep browser console too
  fetch(`${localApiUrl}/network/debug-log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message })
  }).catch(() => {}); // Silent fail if API not available
}

// Proper UTF-8 decoding for base64 data containing multi-byte characters
function decodeBase64UTF8(base64Data) {
  try {
    // Convert base64 to binary string
    const binaryString = atob(base64Data);
    
    // Convert binary string to byte array
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    // Decode UTF-8 bytes to proper string
    return new TextDecoder('utf-8').decode(bytes);
  } catch (error) {
    debugLog(`⚠️ UTF-8 decode error, falling back to atob: ${error.message}`);
    // Fallback to regular atob if UTF-8 decoding fails
    return atob(base64Data);
  }
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
    // console.log('✅ CDP Network domain enabled');
    
    // Enable Runtime domain for better error handling
    await sendCDPCommand(tabId, 'Runtime.enable');
    
    isIntercepting = true;
    
    // Set up event listeners
    chrome.debugger.onEvent.addListener(onCDPEvent);
    
    // Signal readiness to API - CDP is now fully attached and ready
    fetch(`${localApiUrl}/network/ready`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        ready: true, 
        tabId: tabId,
        timestamp: Date.now() 
      })
    }).then(() => {
      debugLog('✅ CDP readiness confirmed with API');
    }).catch(err => {
      debugLog(`⚠️ Failed to signal CDP readiness: ${err}`);
    });
    
    console.log('🟢 CDP network interception started and ready');
    
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
    
    // Reset state
    isIntercepting = false;
    activeTabId = null;
    targetRequestId = null;
    streamBuffer = [];
    lastProcessedData = '';
    chunkQueue = [];
    isProcessingChunks = false;
    completionTriggered = false;
    
    // Reset readiness in API 
    fetch(`${localApiUrl}/network/ready`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        ready: false, 
        timestamp: Date.now() 
      })
    }).catch(() => {}); // Silent fail
    
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
    // console.error('❌ Error handling CDP event:', error);
  }
}

// Handle request will be sent
function handleRequestWillBeSent(params) {
  const url = params.request.url;

  // debugLog(`📤 Request: ${params.requestId} - ${url} (current target: ${targetRequestId})`);

  // ONLY track the actual streaming endpoint, ignore all other DeepSeek API calls
  if (url.includes('/api/v0/chat/completion')) {
    debugLog(`🟡 REAL DeepSeek STREAMING request detected - SETTING TARGET: ${params.requestId}`);
    targetRequestId = params.requestId;
    completionTriggered = false; // Reset completion flag for new request
    
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
async function handleResponseReceived(params) {
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
    
    // Reset stream buffer and chunk processing state
    streamBuffer = [];
    lastProcessedData = '';
    chunkQueue = [];
    isProcessingChunks = false;
    
    try {
      // Enable streaming content to capture SSE data in real-time
      await sendCDPCommand(activeTabId, 'Network.streamResourceContent', {
        requestId: params.requestId
      });
      // debugLog('✅ Streaming content enabled for request: ' + params.requestId);
    } catch (error) {
      debugLog('❌ Failed to enable streaming content: ' + error.message);
    }
    
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
      // console.error('Failed to send response start notification:', err);
    });
  }
}

let lastProcessedData = '';
let chunkQueue = [];
let isProcessingChunks = false;

// Handle data received - now captures actual streaming chunks
async function handleDataReceived(params) {
  if (params.requestId !== targetRequestId) return;
  
  // debugLog(`🟢 Data received for target request: ${params.requestId}, dataLength: ${params.dataLength}`);
  
  // Check if this event contains the actual data chunk
  if (params.data) {
    // Data is base64-encoded in Network.dataReceived events
    // Use proper UTF-8 decoding for multi-byte characters like em-dashes
    const data = decodeBase64UTF8(params.data);
    // debugLog(`🟢 Real-time chunk data (${data.length} chars): ${data.substring(0, 50)}...`);
    
    // Add to queue for sequential processing
    chunkQueue.push(data);
    processChunkQueue();
    
  } else if (params.encodedDataLength || params.dataLength) {
    // Fallback: try to get response body if no direct data
    try {
      const responseBody = await sendCDPCommand(activeTabId, 'Network.getResponseBody', {
        requestId: params.requestId
      });
      
      if (responseBody && responseBody.body) {
        const data = responseBody.base64Encoded ? 
          decodeBase64UTF8(responseBody.body) : responseBody.body;
        
        // Only process new data (diff-based)
        if (data.length > lastProcessedData.length && data.startsWith(lastProcessedData)) {
          const newData = data.substring(lastProcessedData.length);
          if (newData.trim()) {
            // debugLog(`🟢 Fallback streaming data (${newData.length} chars): ${newData.substring(0, 50)}...`);
            
            // Add to queue for sequential processing
            chunkQueue.push(newData);
            processChunkQueue();
          }
          lastProcessedData = data;
        }
      }
      
    } catch (error) {
      debugLog(`⚠️ Could not get response body: ${error.message}`);
    }
  }
}

// Process chunk queue sequentially to maintain order
async function processChunkQueue() {
  if (isProcessingChunks) return; // Already processing
  
  isProcessingChunks = true;
  
  while (chunkQueue.length > 0) {
    const chunk = chunkQueue.shift();
    
    try {
      // Process chunk sequentially
      await processSSEDataSlowly(chunk);
    } catch (error) {
      debugLog(`❌ Error processing chunk: ${error.message}`);
    }
  }
  
  isProcessingChunks = false;
}

// Note: Polling functions removed - now using direct streaming data capture

// Process SSE data slowly and carefully
async function processSSEDataSlowly(data) {
  const lines = data.split('\n');
  
  for (const line of lines) {
    if (line.trim()) {
      if (line.startsWith('data: ')) {
        const eventData = line.substring(6);
        // debugLog(`📝 Processing SSE Data: ${eventData.substring(0, 50)}...`);
        
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
        // debugLog(`🎯 Processing SSE Event: ${eventType}`);
        
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
        
        // Detect completion based on actual SSE events from DeepSeek
        if (eventType === 'finish') {
          debugLog('🟢 SSE finish event detected - checking if completion already triggered');
          if (!completionTriggered) {
            completionTriggered = true;
            debugLog('🟢 SSE completion handler winning - triggering completion after queue empties');
            await waitForQueueAndTriggerCompletion();
          } else {
            debugLog('🟡 SSE completion handler - completion already triggered by network event, skipping');
          }
        }
      }
    }
  }
}

// Handle loading finished
async function handleLoadingFinished(params) {
  debugLog(`📥 Loading finished: ${params.requestId} (target: ${targetRequestId})`);
  
  if (params.requestId !== targetRequestId) {
    debugLog(`⚠️ Ignoring loadingFinished for non-target request ${params.requestId}`);
    return;
  }
  
  debugLog('🟢 Loading finished for DeepSeek API request - checking if completion already triggered');
  
  // Check if completion was already triggered by SSE event
  if (completionTriggered) {
    debugLog('🟡 Network completion handler - completion already triggered by SSE event, skipping');
    return;
  }
  
  completionTriggered = true;
  debugLog('🟢 Network completion handler winning - WAITING FOR QUEUE TO EMPTY');
  
  // Wait for all chunks to be processed before marking complete
  // This prevents race condition where completion signal arrives before all data is processed
  const maxWaitTime = 10000; // 10 second maximum wait
  const startTime = Date.now();
  
  while ((chunkQueue.length > 0 || isProcessingChunks) && (Date.now() - startTime < maxWaitTime)) {
    // debugLog(`⏳ Waiting for chunk queue to empty... (queue: ${chunkQueue.length}, processing: ${isProcessingChunks})`);
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  if (chunkQueue.length > 0 || isProcessingChunks) {
    debugLog(`⚠️ Timeout waiting for chunks to process - proceeding anyway (queue: ${chunkQueue.length}, processing: ${isProcessingChunks})`);
  } else {
    debugLog('✅ All chunks processed - MARKING COMPLETE');
  }
  
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
  lastProcessedData = '';
  chunkQueue = [];
  isProcessingChunks = false;
  completionTriggered = false;
}

// Wait for queue to empty and trigger completion (based on SSE events)
async function waitForQueueAndTriggerCompletion() {
  debugLog('🟢 Waiting for chunk queue to empty before triggering completion...');
  
  const maxWaitTime = 10000; // 10 second maximum wait
  const startTime = Date.now();
  
  while ((chunkQueue.length > 0 || isProcessingChunks) && (Date.now() - startTime < maxWaitTime)) {
    debugLog(`⏳ Waiting for chunk queue to empty before completion... (queue: ${chunkQueue.length}, processing: ${isProcessingChunks})`);
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  if (chunkQueue.length > 0 || isProcessingChunks) {
    debugLog(`⚠️ Timeout waiting for chunks before completion - proceeding anyway (queue: ${chunkQueue.length}, processing: ${isProcessingChunks})`);
  } else {
    debugLog('✅ All chunks processed before completion - MARKING COMPLETE');
  }
  
  // Notify local API about response end
  fetch(`${localApiUrl}/network/response-end`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      requestId: targetRequestId,
      timestamp: Date.now()
    })
  }).catch(err => {
    debugLog(`❌ Failed to send completion notification: ${err}`);
  });
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
    // console.error('Failed to send error notification:', err);
  });
  
  // Reset for next request
  targetRequestId = null;
  streamBuffer = [];
  lastProcessedData = '';
  chunkQueue = [];
  isProcessingChunks = false;
  completionTriggered = false;
}

// Handle EventSource messages (the proper way!)
function handleEventSourceMessage(params) {
  // console.log('🟢 EventSource message received:', params);
  
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
    // console.error('Failed to forward EventSource data:', err);
  });
}

// Parse and forward streaming data
function parseAndForwardStreamData(data) {
  // debugLog(`🔄 Parsing streaming data: ${data.substring(0, 200)}...`);
  
  // Split by newlines to handle SSE format
  const lines = data.split('\n');
  
  for (const line of lines) {
    if (line.trim()) {
      if (line.startsWith('data: ')) {
        const eventData = line.substring(6); // Remove 'data: ' prefix
        // debugLog(`📝 SSE Data: ${eventData.substring(0, 100)}...`);
        
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
        // debugLog(`🎯 SSE Event: ${eventType}`);
        
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
    lastProcessedData = '';
    chunkQueue = [];
    isProcessingChunks = false;
    completionTriggered = false;
  }
});

console.log('CDP Network Interceptor background script initialized');