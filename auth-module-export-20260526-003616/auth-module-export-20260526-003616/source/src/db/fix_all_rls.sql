-- Enable RLS for all tables
alter table public.profiles enable row level security;
alter table public.posts enable row level security;
alter table public.comments enable row level security;
alter table public.interactions enable row level security;
alter table if exists public.messages enable row level security;
alter table if exists public.follows enable row level security;

alter table public.profiles
  add column if not exists role text default 'user';

update public.profiles
set role = 'user'
where role is null;

alter table public.profiles
  alter column role set default 'user';

alter table public.comments
  add column if not exists is_deleted boolean not null default false,
  add column if not exists deleted_at timestamp with time zone,
  add column if not exists deleted_by uuid references public.profiles(id);

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

-- 1. Profiles Policies
drop policy if exists "Public profiles are viewable by everyone" on public.profiles;
drop policy if exists "Public profiles are viewable by everyone." on public.profiles;
create policy "Public profiles are viewable by everyone" on public.profiles for select using (true);

drop policy if exists "Users can insert their own profile" on public.profiles;
drop policy if exists "Users can insert their own profile." on public.profiles;
create policy "Users can insert their own profile" on public.profiles for insert with check (
  auth.uid() = id
  and coalesce(role, 'user') = 'user'
);

drop policy if exists "Users can update own profile" on public.profiles;
drop policy if exists "Users can update own profile." on public.profiles;
create policy "Users can update own profile" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

create or replace function public.prevent_profile_role_self_update()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
begin
  if auth.uid() = new.id and new.role is distinct from old.role then
    raise exception 'profile role cannot be changed by the profile owner';
  end if;

  return new;
end;
$$;

drop trigger if exists prevent_profile_role_self_update on public.profiles;
create trigger prevent_profile_role_self_update
before update of role on public.profiles
for each row execute function public.prevent_profile_role_self_update();

revoke execute on function public.prevent_profile_role_self_update() from anon, authenticated;

-- 2. Posts Policies
drop policy if exists "Posts are viewable by everyone" on public.posts;
drop policy if exists "Posts are viewable by everyone." on public.posts;
create policy "Posts are viewable by everyone" on public.posts for select using (true);

drop policy if exists "Users can insert their own posts" on public.posts;
drop policy if exists "Users can insert their own posts." on public.posts;
drop policy if exists "Users can update their own posts" on public.posts;
drop policy if exists "Users can update their own posts." on public.posts;
drop policy if exists "Users and staff can delete posts" on public.posts;
drop policy if exists "Users and staff can delete posts." on public.posts;

-- Post writes go through the Django community API, where rich text is
-- sanitized and ownership/staff permissions are verified server-side.

-- 3. Comments Policies
drop policy if exists "Comments are viewable by everyone" on public.comments;
drop policy if exists "Comments are viewable by everyone." on public.comments;
create policy "Comments are viewable by everyone" on public.comments for select using (coalesce(is_deleted, false) = false);

drop policy if exists "Authenticated users can insert comments" on public.comments;
drop policy if exists "Authenticated users can insert comments." on public.comments;

drop policy if exists "Users can delete their own comments" on public.comments;
drop policy if exists "Users can delete their own comments." on public.comments;
drop policy if exists "Comment owners and staff can soft delete comments" on public.comments;

-- Comment writes go through the Django community API, which performs soft
-- deletion only after verifying owner/staff permissions.

-- 4. Interactions Policies
drop policy if exists "Interactions are viewable by everyone" on public.interactions;
create policy "Interactions are viewable by everyone" on public.interactions for select using (true);

drop policy if exists "Authenticated users can insert interactions" on public.interactions;
drop policy if exists "Authenticated users can insert interactions." on public.interactions;
create policy "Authenticated users can insert interactions" on public.interactions for insert with check (
  auth.uid() = user_id
  and not exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Users can delete their own interactions" on public.interactions;
drop policy if exists "Users can delete their own interactions." on public.interactions;
create policy "Users can delete their own interactions" on public.interactions for delete using (
  auth.uid() = user_id
  and not exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

-- 5. Messages Policies
drop policy if exists "Users can view their own messages" on public.messages;
drop policy if exists "Users can view their own messages." on public.messages;
create policy "Users can view their own messages" on public.messages for select using (auth.uid() = sender_id or auth.uid() = receiver_id);

drop policy if exists "Users can insert messages" on public.messages;
drop policy if exists "Users can insert messages." on public.messages;
create policy "Users can insert messages" on public.messages for insert with check (
  auth.uid() = sender_id
  and char_length(content) <= 2000
  and type in ('text', 'image')
  and not exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Users can mark received messages read" on public.messages;
create policy "Users can mark received messages read" on public.messages for update using (
  auth.uid() = receiver_id
) with check (
  auth.uid() = receiver_id
  and not exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

-- 6. Follows Policies
drop policy if exists "Follows are viewable by everyone" on public.follows;
create policy "Follows are viewable by everyone" on public.follows for select using (true);

drop policy if exists "Authenticated users can follow others" on public.follows;
create policy "Authenticated users can follow others" on public.follows for insert with check (
  auth.uid() = follower_id
  and follower_id <> following_id
  and not exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);

drop policy if exists "Users can unfollow" on public.follows;
create policy "Users can unfollow" on public.follows for delete using (
  auth.uid() = follower_id
  and not exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'banned'
  )
);
