-- Haftalık ücretsiz plan hakkı tablosu (Supabase > SQL Editor'a yapıştırıp Run).
-- Her başarılı plan için bir satır. Kullanıcı sadece KENDİ satırlarını görür ve ekler;
-- silme/güncelleme izni yok, yani hak sıfırlanamaz. Sunucu gizli anahtar kullanmaz.
create table if not exists public.plan_kullanim (
  id bigint generated always as identity primary key,
  kullanici_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  olusturma timestamptz not null default now()
);

create index if not exists plan_kullanim_kullanici_zaman on public.plan_kullanim (kullanici_id, olusturma);

-- Proje "yeni tablolara otomatik API erişimi" kapalı kuruldu: sadece giriş yapmış kullanıcılara,
-- sadece okuma ve ekleme izni ver (giriş yapmamış "anon" rolüne hiçbir izin yok; silme/güncelleme yok)
revoke all on public.plan_kullanim from anon, authenticated;
grant select, insert on public.plan_kullanim to authenticated;

alter table public.plan_kullanim enable row level security;

drop policy if exists "kendi kayitlarini gorur" on public.plan_kullanim;
create policy "kendi kayitlarini gorur" on public.plan_kullanim
  for select to authenticated using (kullanici_id = auth.uid());

drop policy if exists "kendi kaydini ekler" on public.plan_kullanim;
create policy "kendi kaydini ekler" on public.plan_kullanim
  for insert to authenticated with check (kullanici_id = auth.uid());

-- Hesap silme (Apple ve Google, hesap açılabilen uygulamada uygulama içinden silmeyi zorunlu tutar).
-- Giriş yapmış kullanıcı SADECE kendi hesabını silebilir; plan_kullanim satırları "on delete cascade"
-- ile birlikte silinir. security definer: fonksiyon auth.users'a yetkili olarak erişir, ama içinde
-- yalnızca auth.uid() (isteği yapan kişi) kullanılır. Sunucuya gizli anahtar gerekmez.
create or replace function public.hesabi_sil()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'Giriş yapılmamış';
  end if;
  delete from auth.users where id = auth.uid();
end;
$$;

revoke all on function public.hesabi_sil() from public, anon;
grant execute on function public.hesabi_sil() to authenticated;
