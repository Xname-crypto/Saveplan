-- Block banned users from direct Supabase writes on interactive tables.
-- Run this after the base schema and previous security hardening scripts.

begin;

alter table if exists public.messages enable row level security;
alter table if exists public.interactions enable row level security;
alter table if exists public.follows enable row level security;

do $$
begin
  if to_regclass('public.messages') is not null and not exists (
    select 1
    from pg_constraint
    where conname = 'messages_content_length'
      and conrelid = 'public.messages'::regclass
  ) then
    alter table public.messages
      add constraint messages_content_length check (char_length(content) <= 2000);
  end if;
end;
$$;

drop policy if exists "Users can view their own messages" on public.messages;
drop policy if exists "Users can view their own messages." on public.messages;
create policy "Users can view their own messages"
on public.messages for select
using (auth.uid() = sender_id or auth.uid() = receiver_id);

drop policy if exists "Users can insert messages" on public.messages;
drop policy if exists "Users can insert messages." on public.messages;
create policy "Users can insert messages"
on public.messages for insert
with check (
  auth.uid() = sender_id
  and char_length(content) <= 2000
  and type in ('text', 'image')
  and not exists (
    select 1
    from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Users can mark received messages read" on public.messages;
create policy "Users can mark received messages read"
on public.messages for update
using (auth.uid() = receiver_id)
with check (
  auth.uid() = receiver_id
  and not exists (
    select 1
    from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Authenticated users can insert interactions" on public.interactions;
drop policy if exists "Authenticated users can insert interactions." on public.interactions;
create policy "Authenticated users can insert interactions"
on public.interactions for insert
with check (
  auth.uid() = user_id
  and not exists (
    select 1
    from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Users can delete their own interactions" on public.interactions;
drop policy if exists "Users can delete their own interactions." on public.interactions;
create policy "Users can delete their own interactions"
on public.interactions for delete
using (
  auth.uid() = user_id
  and not exists (
    select 1
    from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Authenticated users can follow others" on public.follows;
create policy "Authenticated users can follow others"
on public.follows for insert
with check (
  auth.uid() = follower_id
  and follower_id <> following_id
  and not exists (
    select 1
    from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Users can unfollow" on public.follows;
create policy "Users can unfollow"
on public.follows for delete
using (
  auth.uid() = follower_id
  and not exists (
    select 1
    from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

commit;
