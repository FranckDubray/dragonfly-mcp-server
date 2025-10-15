/**
 * Workers Session - State (globals only)
 * Doit être chargé avant les autres modules session.*
 */

// Etat global session (partagé entre modules)
let currentWorkerConfig = null;
let ws = null;
let sessionId = null;
let localStream = null;
let micMuted = false;
let currentWorkerIdMemo = null;

// State de conversation
let currentResponseId = null;
let responseCreatePending = false;
window.isUserSpeaking = false;
let systemMessageSent = false;
let autoGreetingTimer = null;
let userHasSpoken = false;
let firstTurnTriggered = false;
let sessionActive = false;
let gotFirstAIAudio = false;
let assistantBuffer = ""; // buffer transcript assistant

// Marqueur debug
window.__workersSessionState = { ready: true };
