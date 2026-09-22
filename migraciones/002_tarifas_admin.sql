-- Migracion 002: rol admin, tarifas con historial, configuracion,
-- actividades multiples por socio y desglose de cuotas.
-- Correr una sola vez en el SQL editor de Supabase, despues de schema.sql.

-- 1) Rol admin
alter table usuarios drop constraint usuarios_rol_check;
alter table usuarios add constraint usuarios_rol_check
  check (rol in ('recepcion','comision','socio','admin'));

-- 2) Eventos de auditoria nuevos
alter table eventos_sistema drop constraint eventos_sistema_tipo_check;
alter table eventos_sistema add constraint eventos_sistema_tipo_check
  check (tipo in ('alta_socio','baja_socio','pago','edicion',
                  'cambio_tarifa','cambio_config','generacion_cuotas'));

-- 3) Un socio puede practicar mas de una actividad
create table socios_actividades (
  socio_id uuid not null references socios(id),
  disciplina text not null check (disciplina in ('basquet','futbol','hockey')),
  primary key (socio_id, disciplina)
);

insert into socios_actividades (socio_id, disciplina)
select id, disciplina_principal from socios
where disciplina_principal in ('basquet','futbol','hockey');

-- 4) Tarifas con historial: nunca se editan, se carga una fila nueva con
--    su fecha de vigencia. El valor actual es la fila no anulada mas
--    reciente con vigente_desde <= hoy.
create table tarifas (
  id uuid primary key default gen_random_uuid(),
  tipo text not null check (tipo in ('societaria','actividad')),
  clave text not null,  -- categoria de socio (societaria) o disciplina (actividad)
  monto numeric(10,2) not null check (monto >= 0),
  vigente_desde date not null,
  anulada boolean not null default false,
  creado_por uuid references usuarios(id),
  creado_en timestamptz not null default now()
);

create unique index tarifas_vigencia_uq
  on tarifas (tipo, clave, vigente_desde) where not anulada;

insert into tarifas (tipo, clave, monto, vigente_desde)
select 'societaria', categoria_socio, monto_base, vigente_desde
from categorias_cuota;

-- 5) Configuracion (dia de vencimiento y recargo)
create table configuracion (
  clave text primary key,
  valor text not null,
  actualizado_en timestamptz not null default now(),
  actualizado_por uuid references usuarios(id)
);

insert into configuracion (clave, valor) values
  ('dia_vencimiento', '10'),
  ('recargo_tipo', 'porcentaje'),  -- 'porcentaje' o 'monto'
  ('recargo_valor', '10');

-- 6) Desglose de la cuota (monto = societaria + actividades)
alter table cuotas
  add column monto_societaria numeric(10,2) not null default 0,
  add column monto_actividad numeric(10,2) not null default 0;

-- 7) Solo el servidor (service key) toca estas tablas
alter table tarifas enable row level security;
alter table configuracion enable row level security;
alter table socios_actividades enable row level security;
