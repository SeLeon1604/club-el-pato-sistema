# Club El Pato - esqueleto del sistema

Backend unico (Flask + Supabase) sirviendo 3 PWA distintas segun el rol
del usuario logueado:

| App | Ruta | Rol | Uso |
|---|---|---|---|
| Recepcion | `/recepcion` | `recepcion` | Tablet: busqueda, cobro de cuotas, alta/baja de socios |
| Comision | `/comision` | `comision` | Celular de Cristian y comision: caja del periodo y erogaciones, solo lectura |
| Carnet del socio | `/carnet` | `socio` | Celular del socio: carnet + QR, novedades (partidos y eventos), beneficios |
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
export SUPABASE_KEY="tu-service-key"
```

y correr `schema.sql` en el SQL editor de Supabase para crear las tablas.

## Usuarios y base de datos

- Correr `schema.sql` y despues, en orden, las migraciones de la
  carpeta `migraciones/` (002, 003, 004...) en Supabase.
- Usar la **service key** en `SUPABASE_KEY` y definir `SECRET_KEY`.
  Esta app no usa Supabase Auth (el login es propio, con sesion de
  Flask), asi que el backend siempre pasa por la service key - por
  eso las tablas tienen RLS habilitado sin policies: no afecta al
  backend, pero cierra el paso a la anon key si algun dia se usa o
  se filtra (ver el comentario en `schema.sql`).
- Crear usuarios con hash: `python crear_usuario.py <rol> <email|dni>`
  (recepcion usa PIN por persona; el resto contrasena).
- Modo demo: `recepcion@elpato.local`/1234, `comision@elpato.local`,
  `admin@elpato.local` y socio DNI 30123456, los tres con `demo1234`.

## Constancia de pago por email (opcional)

Sin configurar nada, el cobro en recepcion sigue dejando el PDF
disponible para ver/descargar y compartir (Web Share API); para que
tambien se pueda mandar por mail hay que definir:

```bash
export EMAIL_PROVIDER="resend"          # o "smtp"
export EMAIL_FROM="recibos@clubelpato.com"
# si EMAIL_PROVIDER=resend
export RESEND_API_KEY="re_..."
# si EMAIL_PROVIDER=smtp
export SMTP_HOST="smtp.miproveedor.com"
export SMTP_PORT="587"
export SMTP_USER="..."
export SMTP_PASSWORD="..."
```

Opcionalmente `CLUB_NOMBRE`, `CLUB_DIRECCION` y `CLUB_CUIT` para el
encabezado del PDF (por defecto `CLUB_NOMBRE="Club El Pato"`).

## Huso horario

El panel de comision calcula "hoy/esta semana/este mes" segun
`CLUB_TZ` (por defecto `America/Argentina/Buenos_Aires`), no segun el
huso del servidor: en produccion suele correr en UTC, y sin esto un
cobro de la tarde/noche quedaba afuera de la caja del dia por caer del
lado equivocado del corte en UTC.

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
- Grupo familiar: si el socio pertenece a uno, la ficha de cobro
  tambien trae las cuotas pendientes de los demas integrantes (con
  checkbox) para cobrarlas todas juntas en un solo pago. Al confirmar
  el cobro queda una constancia en PDF (descargable, por email si hay
  un proveedor configurado, o para compartir por WhatsApp).

## Estructura

```
app.py                  punto de entrada, arma la app y registra blueprints
config.py                lee variables de entorno
db.py                     capa de acceso a datos (Supabase o demo en memoria)
cuotas.py                 logica de negocio: tarifas, generacion y recargo de cuotas
resumen.py                logica de negocio: caja del periodo para comision
recibo.py                 arma el PDF de la constancia de pago y lo manda por mail
schema.sql               creacion de tablas + esqueleto de RLS
migraciones/              cambios incrementales sobre schema.sql, en orden
blueprints/
  auth.py                 login unico, redirige segun rol
  recepcion.py            busqueda, ficha+cobro (individual y familiar), alta/baja de socio
  comision.py             caja del periodo (cobrado, altas/bajas, erogaciones)
  socio.py                carnet + novedades (partidos y eventos) + beneficios
  admin.py                tarifas, configuracion y generacion de cuotas
  erogaciones.py           carga de gastos, compartido entre comision y recepcion
templates/                un HTML simple por pantalla (sin JS pesado todavia)
static/
  manifest_recepcion.json  manifest PWA de la tablet
  manifest_comision.json   manifest PWA de comision
  manifest_socio.json      manifest PWA del socio
  sw.js                    service worker (shell offline, sin cache de escrituras)
  css/style.css            estilos base, pensado para dedo no mouse
  js/qrcode.min.js         genera el QR del carnet (davidshimjs/qrcodejs, MIT)
  js/jsqr.min.js           lee el QR desde la camara (cozmo/jsQR, MIT)
```

## Carnet QR y fixture/auspiciantes

- El carnet del socio muestra un QR real generado en el cliente a partir
  de `carnet_qr.codigo_hash` (se crea la primera vez que se ve el carnet;
  no contiene datos del socio). En recepcion, el boton "Escanear carnet"
  abre la camara y busca al socio por ese codigo.
- Fixture y auspiciantes ya tienen pantalla en `/admin` (cargar partido,
  registrar resultado, cargar y editar auspiciante). Ya no hace falta
  insertarlos a mano en Supabase.

## Pendiente (a definir en las proximas iteraciones)

- **Iconos de la PWA**: los manifests apuntan a `/static/icons/` que
  todavia no tiene los PNG (192x192 y 512x512).
- **Responsable de grupo familiar no-socio**: por ahora el
  responsable de un grupo familiar siempre es un socio (categoria
  `adherente` si no practica ninguna actividad). Queda pendiente de
  confirmar con el club si hace falta soportar un responsable que no
  sea socio.
