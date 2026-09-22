# Club El Pato - esqueleto del sistema

Backend unico (Flask + Supabase) sirviendo 3 PWA distintas segun el rol
del usuario logueado:

| App | Ruta | Rol | Uso |
|---|---|---|---|
| Recepcion | `/recepcion` | `recepcion` | Tablet: busqueda, cobro de cuotas, alta/baja de socios |
| Comision | `/comision` | `comision` | Celular de Cristian y comision: novedades, solo lectura |
| Carnet del socio | `/carnet` | `socio` | Celular del socio: carnet + QR, novedades, auspiciantes |
| Administracion | `/admin` | `admin` | Tarifas con historial, vencimiento y recargo, generacion de cuotas |

## Como correrlo localmente

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Sin variables de entorno configuradas, el proyecto arranca en
**MODO_DEMO** (ver `config.py` / `db.py`): usa datos de ejemplo en
memoria en vez de conectarse a Supabase, para poder ver las pantallas
funcionando sin tener la base todavia.

Para conectar Supabase de verdad, definir:

```bash
export SUPABASE_URL="https://tu-proyecto.supabase.co"
export SUPABASE_KEY="tu-anon-key"
```

y correr `schema.sql` en el SQL editor de Supabase para crear las tablas.

## Usuarios y base de datos

- Correr `schema.sql` y despues `migraciones/002_tarifas_admin.sql` en Supabase.
- Usar la **service key** en `SUPABASE_KEY` y definir `SECRET_KEY`.
- Crear usuarios con hash: `python crear_usuario.py <rol> <email|dni>`
  (recepcion usa PIN por persona; el resto contrasena).
- Modo demo: `recepcion@elpato.local`/1234, `comision@elpato.local`,
  `admin@elpato.local` y socio DNI 30123456, los tres con `demo1234`.

## Cuotas

cuota = tarifa societaria de la categoria + tarifa de cada actividad del
socio (sin tarifa vale $0; si el total es $0 no se genera cuota). Las
tarifas no se editan: se carga un valor nuevo con fecha de vigencia y el
anterior queda en el historial. La cuota usa las tarifas vigentes al dia 1
de su periodo.

- Generar el mes: boton en `/admin` o `python generar_cuotas.py [AAAA-MM]`
  (cron el dia 1). Es idempotente.
- Vencimiento: un dia fijo para todos, configurable. Pasado ese dia la
  cuota pasa a `vencido` y se le fija el recargo (porcentaje o monto) una
  sola vez, al abrir la ficha o al correr la generacion.

## Estructura

```
app.py                  punto de entrada, arma la app y registra blueprints
config.py                lee variables de entorno
db.py                     capa de acceso a datos (Supabase o demo en memoria)
schema.sql               creacion de tablas + esqueleto de RLS
blueprints/
  auth.py                 login unico, redirige segun rol
  recepcion.py            busqueda, ficha+cobro, alta/baja de socio
  comision.py             panel de novedades (solo lectura)
  socio.py                carnet digital + novedades + auspiciantes
templates/                un HTML simple por pantalla (sin JS pesado todavia)
static/
  manifest_recepcion.json  manifest PWA de la tablet
  manifest_comision.json   manifest PWA de comision
  manifest_socio.json      manifest PWA del socio
  sw.js                    service worker (shell offline, sin cache de escrituras)
  css/style.css            estilos base, pensado para dedo no mouse
```

## Pendiente (a definir en las proximas iteraciones)

- **Politicas RLS**: el esqueleto esta en `schema.sql` comentado, hay
  que definirlas segun como quede resuelta la autenticacion.
- **QR real del carnet**: hoy es un placeholder visual. Falta generar
  el QR en el cliente (ej. libreria `qrcode.js`) a partir de
  `carnet_qr.codigo_hash`, y en recepcion agregar el lector de camara.
- **Iconos de la PWA**: los manifests apuntan a `/static/icons/` que
  todavia no tiene los PNG (192x192 y 512x512).
- **Resumen de comision**: `db.resumen_comision()` esta resuelto a
  mano en modo demo; en produccion conviene una vista SQL o RPC en
  vez de calcularlo trayendo todo a Python.
