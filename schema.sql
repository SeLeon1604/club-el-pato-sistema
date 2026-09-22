-- Club El Pato - esquema inicial (Supabase / Postgres)
-- Basado en el diagrama de relacion de tablas acordado.

create extension if not exists "pgcrypto";

create table grupos_familiares (
  id uuid primary key default gen_random_uuid(),
  responsable_socio_id uuid,  -- FK a socios, se agrega despues (referencia circular)
  nombre_grupo text
);

create table socios (
  id uuid primary key default gen_random_uuid(),
  nro_socio serial unique,
  nombre text not null,
  apellido text not null,
  dni text unique not null,
  fecha_nacimiento date,
  email text,
  telefono text,
  direccion text,
  categoria text not null check (categoria in ('activo','cadete','vitalicio','honorario','adherente')),
  disciplina_principal text check (disciplina_principal in ('basquet','futbol','hockey','ninguna')),
  grupo_familiar_id uuid references grupos_familiares(id),
  estado text not null default 'activo' check (estado in ('activo','inactivo','suspendido')),
  fecha_alta date not null default current_date,
  fecha_baja date,
  motivo_baja text,
  foto_url text
);

alter table grupos_familiares
  add constraint fk_responsable
  foreign key (responsable_socio_id) references socios(id);

create table categorias_cuota (
  id uuid primary key default gen_random_uuid(),
  categoria_socio text not null,
  monto_base numeric(10,2) not null,
  vigente_desde date not null default current_date
);

create table cuotas (
  id uuid primary key default gen_random_uuid(),
  socio_id uuid not null references socios(id),
  periodo text not null,  -- ej '2026-09'
  monto numeric(10,2) not null,
  monto_recargo numeric(10,2) not null default 0,
  fecha_vencimiento date not null,
  estado text not null default 'pendiente' check (estado in ('pendiente','pagado','vencido','condonado')),
  unique (socio_id, periodo)
);

create table usuarios (
  id uuid primary key default gen_random_uuid(),
  socio_id uuid references socios(id),
  rol text not null check (rol in ('recepcion','comision','socio')),
  email text,
  dni_login text,
  pin_hash text,
  password_hash text,
  activo boolean not null default true
);

create table pagos (
  id uuid primary key default gen_random_uuid(),
  fecha_pago timestamptz not null default now(),
  monto_pagado numeric(10,2) not null,
  medio_pago text not null check (medio_pago in ('efectivo','transferencia','mercadopago','debito')),
  comprobante_url text,
  registrado_por uuid references usuarios(id)
);

create table pagos_cuotas (
  pago_id uuid not null references pagos(id),
  cuota_id uuid not null references cuotas(id),
  primary key (pago_id, cuota_id)
);

create table carnet_qr (
  id uuid primary key default gen_random_uuid(),
  socio_id uuid not null unique references socios(id),
  codigo_hash text not null unique,
  emitido_en timestamptz not null default now(),
  revocado boolean not null default false
);

create table eventos_club (
  id uuid primary key default gen_random_uuid(),
  titulo text not null,
  descripcion text,
  disciplina text check (disciplina in ('basquet','futbol','hockey')),
  fecha_evento timestamptz not null,
  lugar text,
  creado_por uuid references usuarios(id),
  visible_desde timestamptz,
  visible_hasta timestamptz
);

create table auspiciantes (
  id uuid primary key default gen_random_uuid(),
  nombre text not null,
  logo_url text,
  link text,
  orden int not null default 0,
  activo boolean not null default true,
  fecha_desde date,
  fecha_hasta date
);

create table eventos_sistema (
  id uuid primary key default gen_random_uuid(),
  tipo text not null check (tipo in ('alta_socio','baja_socio','pago','edicion')),
  socio_id uuid references socios(id),
  detalle jsonb,
  usuario_id uuid references usuarios(id),
  creado_en timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- Row Level Security (esqueleto - ajustar segun como se resuelva auth)
-- ---------------------------------------------------------------------
alter table socios enable row level security;
alter table cuotas enable row level security;
alter table pagos enable row level security;

-- Ejemplo: recepcion y comision pueden leer todo; el socio solo su fila.
-- Esto asume que el JWT trae el socio_id y el rol en sus claims
-- (definir esto al implementar la autenticacion real con Supabase Auth).
--
-- create policy "socio_ve_su_propia_ficha" on socios
--   for select using (
--     auth.jwt() ->> 'rol' in ('recepcion','comision')
--     or id = (auth.jwt() ->> 'socio_id')::uuid
--   );

-- Login: un identificador no puede repetirse entre usuarios
create unique index usuarios_email_uq on usuarios (lower(email)) where email is not null;
create unique index usuarios_dni_login_uq on usuarios (dni_login) where dni_login is not null;
