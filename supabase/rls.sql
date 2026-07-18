-- Supabase RLS draft for private tables.
-- Apply after creating full production migrations.

alter table if exists bankrolls enable row level security;
alter table if exists events enable row level security;
alter table if exists sportsbooks enable row level security;
alter table if exists bets enable row level security;
alter table if exists postmortems enable row level security;

create policy if not exists "Users own bankrolls"
on bankrolls for all
using (auth.uid()::text = user_id)
with check (auth.uid()::text = user_id);

create policy if not exists "Users own events"
on events for all
using (auth.uid()::text = user_id)
with check (auth.uid()::text = user_id);

create policy if not exists "Users own bets"
on bets for all
using (auth.uid()::text = user_id)
with check (auth.uid()::text = user_id);
