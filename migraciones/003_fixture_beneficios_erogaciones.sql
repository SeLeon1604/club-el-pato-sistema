-- Migracion 003: fixture de partidos, beneficios de auspiciantes,
-- erogaciones (gastos) y numero de recibo para los pagos.
-- Correr una sola vez en el SQL editor de Supabase, despues de 002.

-- 1) Fixture de partidos (para "Proximos partidos" en la app del socio)
create table fixture (
  id uuid primary key default gen_random_uuid(),
  disciplina text not null check (disciplina in ('basquet','futbol','hockey')),
  categoria text not null,
  rival text not null,
  fecha_hora timestamptz not null,
  lugar text,
  condicion text not null check (condicion in ('local','visitante')),
  resultado_propio int,
  resultado_rival int
);

-- 2) Beneficios de los auspiciantes (para la pestaña "Beneficios")
alter table auspiciantes
  add column descripcion_beneficio text,
  add column codigo_descuento text,
  add column categoria_comercio text;

-- 3) Erogaciones (gastos del club, para el panel de comision)
create table erogaciones (
  id uuid primary key default gen_random_uuid(),
  concepto text not null,
  categoria text,
  monto numeric(10,2) not null check (monto >= 0),
  fecha date not null default current_date,
  registrado_por uuid references usuarios(id)
);

-- 4) Numero de recibo legible y correlativo (el id de pagos es uuid)
alter table pagos add column numero bigserial unique;

-- 5) Nuevo tipo de evento de auditoria para las erogaciones
alter table eventos_sistema drop constraint eventos_sistema_tipo_check;
alter table eventos_sistema add constraint eventos_sistema_tipo_check
  check (tipo in ('alta_socio','baja_socio','pago','edicion',
                  'cambio_tarifa','cambio_config','generacion_cuotas',
                  'erogacion'));

-- 6) Solo el servidor (service key) toca las erogaciones
alter table erogaciones enable row level security;
