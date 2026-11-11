-- Migracion 004: RLS en el resto de las tablas.
-- Correr una sola vez en el SQL editor de Supabase, despues de 003.
--
-- Ver el comentario en schema.sql: esta app no usa Supabase Auth, el
-- backend siempre habla con Supabase por la service key (que ignora
-- RLS) y no hay ningun flujo que use la anon key. Habilitar RLS sin
-- policies no cambia nada para el backend, pero cierra estas tablas
-- para cualquiera que use la anon key (filtrada, o agregada a futuro
-- del lado del cliente via supabase-js).

alter table grupos_familiares enable row level security;
alter table categorias_cuota enable row level security;
alter table usuarios enable row level security;
alter table pagos_cuotas enable row level security;
alter table carnet_qr enable row level security;
alter table eventos_club enable row level security;
alter table auspiciantes enable row level security;
alter table eventos_sistema enable row level security;
alter table fixture enable row level security;
