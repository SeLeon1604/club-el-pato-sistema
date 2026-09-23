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
export SUPABASE_KEY="tu-anon-key"
```

y correr `schema.sql` en el SQL editor de Supabase para crear las tablas.

## Usuarios y base de datos

- Correr `schema.sql` y despues, en orden, las migraciones de la
  carpeta `migraciones/` (002, 003...) en Supabase.
- Usar la **service key** en `SUPABASE_KEY` y definir `SECRET_KEY`.
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
```

## Pendiente (a definir en las proximas iteraciones)

- **Politicas RLS**: el esqueleto esta en `schema.sql` comentado, hay
  que definirlas segun como quede resuelta la autenticacion.
- **QR real del carnet**: hoy es un placeholder visual. Falta generar
  el QR en el cliente (ej. libreria `qrcode.js`) a partir de
  `carnet_qr.codigo_hash`, y en recepcion agregar el lector de camara.
- **Iconos de la PWA**: los manifests apuntan a `/static/icons/` que
  todavia no tiene los PNG (192x192 y 512x512).
- **Carga de fixture y auspiciantes**: todavia no tienen pantalla en
  `/admin`, se cargan directo en las tablas de Supabase (igual que
  hoy con auspiciantes). Si el club las usa seguido conviene agregar
  esas pantallas.
- **Responsable de grupo familiar no-socio**: por ahora el
  responsable de un grupo familiar siempre es un socio (categoria
  `adherente` si no practica ninguna actividad). Queda pendiente de
  confirmar con el club si hace falta soportar un responsable que no
  sea socio.
