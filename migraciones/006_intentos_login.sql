-- Migracion 006: demorar cada vez mas los intentos de login fallidos
-- seguidos (en vez de bloquear al usuario), para frenar la adivinanza
-- por fuerza bruta del PIN de recepcion sin dejar a nadie afuera.
-- Correr una sola vez en el SQL editor de Supabase, despues de 005.

alter table usuarios
  add column intentos_fallidos int not null default 0;
