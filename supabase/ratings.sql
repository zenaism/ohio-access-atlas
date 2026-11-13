-- Community accessibility ratings for the Ohio Access Atlas maps.
--
-- Run once in the Supabase SQL editor (Dashboard -> SQL -> New query -> paste -> Run).
-- Safe to re-run: every statement is idempotent.
--
-- Design
--   * ratings          raw rows, one per (place, device). NOT readable from the browser.
--   * submit_rating()  the only way the public page can write: validates input, rate-limits,
--                      and lets a device change its own earlier rating (upsert).
--   * rating_summary   per-place averages, readable by anyone; this is what the map shows.
-- Comments are stored for research but never published (no moderation needed on the map).
-- No IP address, name or account is stored; device_id is a random id kept in the visitor's browser.

create table if not exists public.ratings (
  id          bigint generated always as identity primary key,
  link_id     text        not null check (link_id ~ '^[a-z0-9-]{1,140}$'),  -- the map's place id
  region      text        not null check (region in ('cincinnati', 'oxford')),
  device_id   uuid        not null,
  overall     smallint    not null check (overall between 1 and 5),
  entrance    smallint             check (entrance between 1 and 5),
  restroom    smallint             check (restroom between 1 and 5),
  parking     smallint             check (parking between 1 and 5),
  inside      smallint             check (inside between 1 and 5),   -- moving around inside / on site
  profile     text                 check (profile in
                ('wheelchair', 'mobility_aid', 'blind_low_vision', 'deaf_hoh', 'other', 'companion')),
  visited     date,                                                 -- first day of the visit month
  comment     text                 check (char_length(comment) <= 500),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (link_id, device_id)
);
create index if not exists ratings_link_idx on public.ratings (link_id);
create index if not exists ratings_device_time_idx on public.ratings (device_id, updated_at);

-- Lock the raw table: browsers (anon/authenticated) can neither read nor write it directly.
alter table public.ratings enable row level security;
revoke all on public.ratings from anon, authenticated;

create or replace function public.submit_rating(
  p_link_id text, p_region text, p_device_id uuid, p_overall int,
  p_entrance int default null, p_restroom int default null, p_parking int default null,
  p_inside int default null, p_profile text default null, p_visited date default null,
  p_comment text default null
) returns void
language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from ratings
        where device_id = p_device_id and updated_at > now() - interval '1 day') >= 40 then
    raise exception 'Too many ratings from this device today; please try again tomorrow.';
  end if;
  if p_visited is not null and (p_visited > current_date or p_visited < date '2000-01-01') then
    raise exception 'Visit date is out of range.';
  end if;
  insert into ratings (link_id, region, device_id, overall, entrance, restroom, parking, inside,
                       profile, visited, comment)
  values (p_link_id, p_region, p_device_id, p_overall, p_entrance, p_restroom, p_parking, p_inside,
          p_profile, p_visited, nullif(trim(p_comment), ''))
  on conflict (link_id, device_id) do update set
    overall = excluded.overall, entrance = excluded.entrance, restroom = excluded.restroom,
    parking = excluded.parking, inside = excluded.inside, profile = excluded.profile,
    visited = excluded.visited, comment = excluded.comment, updated_at = now();
end $$;
revoke all on function public.submit_rating from public;
grant execute on function public.submit_rating to anon, authenticated;

-- Per-place summary. `score` is a Bayesian average that starts at 3 stars (the prior counts
-- as 3 ratings), so one 5-star vote cannot put a place at the top of "Highest community rating".
create or replace view public.rating_summary as
select
  link_id,
  count(*)::int                                   as n,
  round(avg(overall), 2)                          as overall,
  round((3 * 3 + sum(overall)) / (3.0 + count(*)), 3) as score,
  round(avg(entrance), 2) as entrance, count(entrance)::int as n_entrance,
  round(avg(restroom), 2) as restroom, count(restroom)::int as n_restroom,
  round(avg(parking), 2)  as parking,  count(parking)::int  as n_parking,
  round(avg(inside), 2)   as inside,   count(inside)::int   as n_inside,
  round(avg(overall) filter (where profile = 'wheelchair'), 2) as wheelchair,
  count(*) filter (where profile = 'wheelchair')::int           as n_wheelchair,
  round(avg(overall) filter (where profile = 'blind_low_vision'), 2) as blind,
  count(*) filter (where profile = 'blind_low_vision')::int           as n_blind,
  max(updated_at)::date                           as latest
from public.ratings
group by link_id;
grant select on public.rating_summary to anon, authenticated;
