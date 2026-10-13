-- GTM data model. One row per real-world thing; history lives in event tables.

create table accounts (
  account_id      text primary key,          -- normalised domain
  name            text not null,
  hq_country      text,
  employees       integer,
  segment         text,                       -- e.g. vertical_saas, pe_portfolio
  hypothesis      text,                       -- H1, H2 ...
  owner           text,
  created_at      timestamp default current_timestamp
);

create table contacts (
  contact_id      text primary key,
  account_id      text references accounts(account_id),
  full_name       text,
  title           text,
  persona         text,                       -- see playbook/personas.md
  linkedin_url    text,
  email           text,
  email_status    text                        -- verified, catch_all, unknown
);

-- Append-only: every observed signal with its evidence.
create table signals (
  signal_id       text primary key,
  account_id      text references accounts(account_id),
  signal_type     text not null,              -- key in signals/signals.yml
  observed_on     date not null,
  evidence_url    text not null,
  evidence_quote  text,
  source          text                        -- job_board, press_release, deal_db
);

-- Snapshot per scoring run, so score changes can be explained later.
create table account_scores (
  account_id      text references accounts(account_id),
  scored_on       date,
  fit_score       numeric,
  signal_score    numeric,
  total_score     numeric,
  tier            text,                       -- A, B, C
  primary_reason  text,
  primary key (account_id, scored_on)
);

create table touches (
  touch_id        text primary key,
  contact_id      text references contacts(contact_id),
  channel         text,                       -- email, linkedin, intro, event
  sent_on         timestamp,
  template_id     text,
  signal_id       text references signals(signal_id),  -- which signal the message used
  outcome         text                        -- replied, meeting, no_reply, bounced
);

create table deals (
  deal_id         text primary key,
  account_id      text references accounts(account_id),
  source          text,                       -- referral, outbound, inbound, partner
  referred_by     text,
  stage           text,
  value_eur       numeric,
  opened_on       date,
  closed_on       date,
  won             boolean
);

-- Which signals and sources actually turn into won deals.
create view signal_to_win as
select s.signal_type,
       count(distinct d.deal_id)                         as deals,
       count(distinct case when d.won then d.deal_id end) as won
from signals s
join deals d on d.account_id = s.account_id and s.observed_on <= d.opened_on
group by s.signal_type;
