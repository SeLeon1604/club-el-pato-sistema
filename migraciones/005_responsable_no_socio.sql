-- Migracion 005: el responsable de un grupo familiar puede no ser
-- socio (hoy, en la realidad del club, ya pasa).
-- Correr una sola vez en el SQL editor de Supabase, despues de 004.

alter table grupos_familiares
  add column responsable_nombre text,
  add column responsable_dni text,
  add column responsable_telefono text,
  add column responsable_email text;

-- El responsable es o un socio (responsable_socio_id) o una persona
-- sin cargar como socio (responsable_nombre + datos de contacto), no
-- las dos cosas a la vez.
alter table grupos_familiares
  add constraint responsable_uno_solo
  check (responsable_socio_id is null or responsable_nombre is null);
