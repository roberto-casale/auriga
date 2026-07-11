// Service worker "passacarte" di AURIGA.
//
// Serve SOLO a rendere il gioco installabile come PWA: non fa alcuna cache,
// ogni richiesta passa alla rete come sempre. Così un nuovo deploy è subito
// visibile e il comportamento del gioco resta identico a prima.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {
  // nessun respondWith: il browser usa la rete normalmente
});
