create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists immigration_knowledge_base (
  id uuid primary key default gen_random_uuid(),
  country text not null,
  form_type text not null,
  source_url text not null,
  document_url text,
  page_url text,
  last_updated_date date,
  document_hash text not null,
  content_chunk text not null,
  embedding vector(1536) not null,
  created_at timestamp with time zone default now()
);

alter table immigration_knowledge_base add column if not exists document_url text;
alter table immigration_knowledge_base add column if not exists page_url text;
alter table immigration_knowledge_base add column if not exists created_at timestamp with time zone default now();

create table if not exists ingestion_failures (
  id uuid primary key default gen_random_uuid(),
  target_name text,
  source_url text,
  document_url text,
  stage text not null,
  error_type text,
  error_message text,
  created_at timestamp with time zone default now()
);

create table if not exists review_queue (
  id uuid primary key default gen_random_uuid(),
  document_id text,
  provider text,
  status text default 'pending',
  summary text,
  issues jsonb,
  review_required boolean default true,
  review_reasons jsonb,
  risk_score numeric,
  confidence_avg numeric,
  reviewer_notes text,
  tenant_id text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

create or replace function match_immigration_documents(
  query_embedding vector(1536),
  match_count int
)
returns table (
  id uuid,
  country text,
  form_type text,
  source_url text,
  document_url text,
  page_url text,
  last_updated_date date,
  document_hash text,
  content_chunk text,
  similarity float
)
language sql
stable
as $$
  select
    id,
    country,
    form_type,
    source_url,
    document_url,
    page_url,
    last_updated_date,
    document_hash,
    content_chunk,
    1 - (embedding <=> query_embedding) as similarity
  from immigration_knowledge_base
  order by embedding <=> query_embedding
  limit match_count;
$$;
