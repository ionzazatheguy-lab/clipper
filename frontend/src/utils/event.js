// === utils/event.js — Simple Pub/Sub ===

let subscribers = {};

export function on(channel, handler) {
  if (!subscribers[channel]) subscribers[channel] = [];
  subscribers[channel].push(handler);
  return () => {
    subscribers[channel] = subscribers[channel].filter(h => h !== handler);
  };
}

export function off(channel, handler) {
  if (subscribers[channel]) {
    subscribers[channel] = subscribers[channel].filter(h => h !== handler);
  }
}

export function emit(channel, data) {
  if (!subscribers[channel]) return;
  subscribers[channel].forEach(handler => handler(data));
}