-- ============================================================
-- Migração #4: Expansão para a empresa toda
--   1. Setores (departments) + membros
--   2. Datas de início / término nos tickets
--   3. Log de notificações por e-mail (dedupe da automação)
--   4. RLS reescrita: setor fechado, admin vê tudo
--
-- Execute no SQL Editor do Supabase APÓS 01/02/03.
-- Idempotente: pode ser re-executada com segurança.
-- ============================================================

-- ============================================================
-- 1. TABELA: departments (setores da empresa)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    descricao TEXT,
    cor TEXT NOT NULL DEFAULT '#d4a853',
    ativo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 2. TABELA: department_members (quem pertence a qual setor)
--    papel = 'manager' -> pode administrar o setor (membros/exclusões)
--    papel = 'member'  -> colaborador comum do setor
-- ============================================================
CREATE TABLE IF NOT EXISTS public.department_members (
    department_id UUID NOT NULL REFERENCES public.departments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    papel TEXT NOT NULL DEFAULT 'member' CHECK (papel IN ('manager', 'member')),
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (department_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_dept_members_user ON public.department_members(user_id);

-- ============================================================
-- 3. TICKETS: setor + datas de início/término
-- ============================================================
ALTER TABLE public.tickets
    ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES public.departments(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS data_inicio DATE,
    ADD COLUMN IF NOT EXISTS data_fim DATE;

-- Garante coerência: término nunca antes do início
ALTER TABLE public.tickets DROP CONSTRAINT IF EXISTS tickets_datas_coerentes;
ALTER TABLE public.tickets
    ADD CONSTRAINT tickets_datas_coerentes
    CHECK (data_inicio IS NULL OR data_fim IS NULL OR data_fim >= data_inicio);

CREATE INDEX IF NOT EXISTS idx_tickets_department ON public.tickets(department_id);
CREATE INDEX IF NOT EXISTS idx_tickets_data_fim ON public.tickets(data_fim);

-- ============================================================
-- 4. SEED: setor inicial + migração dos dados existentes
--    Todo o histórico atual pertence ao time de TI.
-- ============================================================
INSERT INTO public.departments (nome, slug, descricao, cor)
VALUES ('Núcleo Digital (TI)', 'nucleo-digital', 'Time de Tecnologia da Informação', '#d4a853')
ON CONFLICT (slug) DO NOTHING;

-- Tickets sem setor vão para o Núcleo Digital
UPDATE public.tickets
SET department_id = (SELECT id FROM public.departments WHERE slug = 'nucleo-digital')
WHERE department_id IS NULL;

-- Usuários já cadastrados entram no Núcleo Digital (admins como managers)
INSERT INTO public.department_members (department_id, user_id, papel)
SELECT
    (SELECT id FROM public.departments WHERE slug = 'nucleo-digital'),
    u.id,
    CASE WHEN u.role = 'admin' THEN 'manager' ELSE 'member' END
FROM public.users u
ON CONFLICT (department_id, user_id) DO NOTHING;

-- ============================================================
-- 5. TABELA: ticket_notifications_log
--    Dedupe da automação de e-mail. A UNIQUE abaixo é a garantia
--    de que o mesmo aviso nunca sai duas vezes, mesmo que o
--    scheduler rode em múltiplos workers.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.ticket_notifications_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('due_soon', 'due_today', 'overdue')),
    -- Data de vencimento que originou o aviso: se o prazo for
    -- reagendado, um novo aviso é permitido.
    data_referencia DATE NOT NULL,
    dias_restantes INTEGER,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ticket_id, email, tipo, data_referencia, dias_restantes)
);

CREATE INDEX IF NOT EXISTS idx_notif_log_ticket ON public.ticket_notifications_log(ticket_id);
CREATE INDEX IF NOT EXISTS idx_notif_log_sent_at ON public.ticket_notifications_log(sent_at);

-- ============================================================
-- 6. FUNÇÕES AUXILIARES DE AUTORIZAÇÃO
--    SECURITY DEFINER para não recursar nas próprias policies.
-- ============================================================
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.users
        WHERE id = (SELECT auth.uid()) AND role = 'admin'
    );
$$;

CREATE OR REPLACE FUNCTION public.can_access_department(dept UUID)
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT
        public.is_admin()
        -- Ticket órfão (sem setor) fica visível para não sumir do board
        OR dept IS NULL
        OR EXISTS (
            SELECT 1 FROM public.department_members
            WHERE department_id = dept AND user_id = (SELECT auth.uid())
        );
$$;

CREATE OR REPLACE FUNCTION public.manages_department(dept UUID)
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT
        public.is_admin()
        OR EXISTS (
            SELECT 1 FROM public.department_members
            WHERE department_id = dept
              AND user_id = (SELECT auth.uid())
              AND papel = 'manager'
        );
$$;

CREATE OR REPLACE FUNCTION public.can_access_ticket(tid UUID)
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.tickets t
        WHERE t.id = tid AND public.can_access_department(t.department_id)
    );
$$;

-- ============================================================
-- 7. RLS
-- ============================================================

-- ─── departments: todos leem (para exibir nomes), admin escreve ───
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Setores: leitura autenticada" ON public.departments;
CREATE POLICY "Setores: leitura autenticada"
    ON public.departments FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Setores: escrita admin" ON public.departments;
CREATE POLICY "Setores: escrita admin"
    ON public.departments FOR ALL TO authenticated
    USING (public.is_admin()) WITH CHECK (public.is_admin());

-- ─── department_members ───
ALTER TABLE public.department_members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Membros: leitura autenticada" ON public.department_members;
CREATE POLICY "Membros: leitura autenticada"
    ON public.department_members FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Membros: escrita admin ou gestor do setor" ON public.department_members;
CREATE POLICY "Membros: escrita admin ou gestor do setor"
    ON public.department_members FOR ALL TO authenticated
    USING (public.manages_department(department_id))
    WITH CHECK (public.manages_department(department_id));

-- ─── tickets: setor fechado ───
DROP POLICY IF EXISTS "Tickets: select for authenticated" ON public.tickets;
DROP POLICY IF EXISTS "Tickets: insert for authenticated" ON public.tickets;
DROP POLICY IF EXISTS "Tickets: update for authenticated" ON public.tickets;
DROP POLICY IF EXISTS "Tickets: delete for admin" ON public.tickets;

CREATE POLICY "Tickets: leitura do proprio setor"
    ON public.tickets FOR SELECT TO authenticated
    USING (public.can_access_department(department_id));

CREATE POLICY "Tickets: insert no proprio setor"
    ON public.tickets FOR INSERT TO authenticated
    WITH CHECK (
        (SELECT auth.uid()) IS NOT NULL
        AND public.can_access_department(department_id)
    );

CREATE POLICY "Tickets: update no proprio setor"
    ON public.tickets FOR UPDATE TO authenticated
    USING (public.can_access_department(department_id))
    WITH CHECK (public.can_access_department(department_id));

CREATE POLICY "Tickets: delete admin ou gestor do setor"
    ON public.tickets FOR DELETE TO authenticated
    USING (public.manages_department(department_id));

-- ─── Tabelas filhas seguem o acesso do ticket ───
DROP POLICY IF EXISTS "Participantes: todos authenticated podem ler" ON public.ticket_participants;
DROP POLICY IF EXISTS "Participantes: todos authenticated podem alterar" ON public.ticket_participants;

CREATE POLICY "Participantes: acesso pelo ticket"
    ON public.ticket_participants FOR ALL TO authenticated
    USING (public.can_access_ticket(ticket_id))
    WITH CHECK (public.can_access_ticket(ticket_id));

DROP POLICY IF EXISTS "Anexos: ler" ON public.ticket_attachments;
DROP POLICY IF EXISTS "Anexos: inserir" ON public.ticket_attachments;

CREATE POLICY "Anexos: ler pelo ticket"
    ON public.ticket_attachments FOR SELECT TO authenticated
    USING (public.can_access_ticket(ticket_id));

CREATE POLICY "Anexos: inserir pelo ticket"
    ON public.ticket_attachments FOR INSERT TO authenticated
    WITH CHECK (public.can_access_ticket(ticket_id));
-- (a policy de DELETE de anexos — dono ou admin — permanece como está)

DROP POLICY IF EXISTS "Checklists: select for authenticated" ON public.ticket_checklists;
DROP POLICY IF EXISTS "Checklists: insert for authenticated" ON public.ticket_checklists;
DROP POLICY IF EXISTS "Checklists: update for authenticated" ON public.ticket_checklists;
DROP POLICY IF EXISTS "Checklists: delete for authenticated" ON public.ticket_checklists;

CREATE POLICY "Checklists: acesso pelo ticket"
    ON public.ticket_checklists FOR ALL TO authenticated
    USING (public.can_access_ticket(ticket_id))
    WITH CHECK (public.can_access_ticket(ticket_id));

-- ─── events log: acompanha o ticket ───
DROP POLICY IF EXISTS "Events: select for authenticated" ON public.ticket_events_log;
CREATE POLICY "Events: leitura pelo ticket"
    ON public.ticket_events_log FOR SELECT TO authenticated
    USING (public.can_access_ticket(ticket_id));

-- ─── notifications log: leitura pelo ticket, escrita só service role ───
ALTER TABLE public.ticket_notifications_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Notificacoes: leitura pelo ticket" ON public.ticket_notifications_log;
CREATE POLICY "Notificacoes: leitura pelo ticket"
    ON public.ticket_notifications_log FOR SELECT TO authenticated
    USING (public.can_access_ticket(ticket_id));

-- ============================================================
-- 8. Realtime: o board depende do stream de tickets
-- ============================================================
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE public.tickets;
EXCEPTION WHEN duplicate_object THEN
    NULL;
END $$;
