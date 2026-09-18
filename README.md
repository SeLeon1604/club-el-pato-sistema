# Club El Pato - esqueleto del sistema

Backend unico (Flask + Supabase) sirviendo 3 PWA distintas segun el rol
del usuario logueado:

| App | Ruta | Rol | Uso |
|---|---|---|---|
| Recepcion | `/recepcion` | `recepcion` | Tablet: busqueda, cobro de cuotas, alta/baja de socios |
| Comision | `/comision` | `comision` | Celular de Cristian y comision: novedades, solo lectura |
| Carnet del socio | `/carnet` | `socio` | Celular del socio: carnet + QR, novedades, auspiciantes |

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

- **Autenticacion real**: hoy el login acepta cualquier PIN/password no
  vacio. Falta conectar contra la tabla `usuarios` con hash real
  (bcrypt) y, si se usa Supabase Auth, mapear el JWT a `rol`/`socio_id`.
- **Politicas RLS**: el esqueleto esta en `schema.sql` comentado, hay
  que definirlas segun como quede resuelta la autenticacion.
- **QR real del carnet**: hoy es un placeholder visual. Falta generar
  el QR en el cliente (ej. libreria `qrcode.js`) a partir de
  `carnet_qr.codigo_hash`, y en recepcion agregar el lector de camara.
- **Iconos de la PWA**: los manifests apuntan a `/static/icons/` que
  todavia no tiene los PNG (192x192 y 512x512).
- **Generacion mensual de cuotas**: falta el proceso (cron / funcion
  de Supabase) que crea las cuotas de cada socio cada mes.
- **Resumen de comision**: `db.resumen_comision()` esta resuelto a
  mano en modo demo; en produccion conviene una vista SQL o RPC en
  vez de calcularlo trayendo todo a Python.
