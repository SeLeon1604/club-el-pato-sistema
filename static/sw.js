/*
 * Service worker compartido por las 3 PWA.
 *
 * Estrategia (segun lo hablado): cachear solo lo necesario para que
 * la app *abra* y se pueda *consultar* sin conexion (shell + ultima
 * data vista). El cobro real y el alta/baja de socios requieren red
 * (no se resuelve offline, para evitar conflictos de sincronizacion).
 */
const CACHE_NAME = "club-el-pato-v1";
const ARCHIVOS_SHELL = [
  "/static/css/style.css",
  "/static/manifest_recepcion.json",
  "/static/manifest_comision.json",
  "/static/manifest_socio.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ARCHIVOS_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Nunca cachear operaciones que escriben datos (cobro, alta, baja).
  if (request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const red = fetch(request)
        .then((respuesta) => {
          caches.open(CACHE_NAME).then((cache) => cache.put(request, respuesta.clone()));
          return respuesta;
        })
        .catch(() => cached);
      return cached || red;
    })
  );
});
