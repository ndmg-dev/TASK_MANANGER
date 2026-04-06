-- ============================================================
-- NDMG Task Manager — Schema SQL
-- Executar no SQL Editor do Supabase
-- ============================================================

-- ============================================================
-- 1. TABELA: users (perfil vinculado ao Supabase Auth)
-- ============================================================
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'developer'
        CHECK (role IN ('admin', 'developer', 'viewer')),
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trigger: cria perfil automaticamente ao criar conta no Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, full_name, email, avatar_url)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        NEW.email,
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- 2. TABELA: tickets
-- ============================================================
CREATE TABLE public.tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo TEXT NOT NULL,
    descricao TEXT,
    status TEXT NOT NULL DEFAULT 'Backlog'
        CHECK (status IN ('Backlog', 'To Do', 'In Progress', 'In Review', 'Done')),
    prioridade TEXT NOT NULL DEFAULT 'medium'
        CHECK (prioridade IN ('low', 'medium', 'high', 'critical')),
    assignee_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tickets_status ON public.tickets(status);
CREATE INDEX idx_tickets_assignee ON public.tickets(assignee_id);
CREATE INDEX idx_tickets_created_at ON public.tickets(created_at);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON public.tickets
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ============================================================
-- 3. TABELA: ticket_events_log (event sourcing para métricas)
-- ============================================================
CREATE TABLE public.ticket_events_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    status_anterior TEXT,
    status_novo TEXT NOT NULL,
    changed_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_events_ticket ON public.ticket_events_log(ticket_id);
CREATE INDEX idx_events_timestamp ON public.ticket_events_log(timestamp);
CREATE INDEX idx_events_status_novo ON public.ticket_events_log(status_novo);

-- Trigger: registra evento automaticamente ao mudar status
CREATE OR REPLACE FUNCTION public.log_ticket_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO public.ticket_events_log (ticket_id, status_anterior, status_novo, changed_by)
        VALUES (NEW.id, OLD.status, NEW.status, (select auth.uid()));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_ticket_status_change
    AFTER UPDATE ON public.tickets
    FOR EACH ROW EXECUTE FUNCTION public.log_ticket_status_change();

-- Trigger: registra criação do ticket como primeiro evento
CREATE OR REPLACE FUNCTION public.log_ticket_creation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.ticket_events_log (ticket_id, status_anterior, status_novo, changed_by)
    VALUES (NEW.id, NULL, NEW.status, NEW.created_by);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_ticket_created
    AFTER INSERT ON public.tickets
    FOR EACH ROW EXECUTE FUNCTION public.log_ticket_creation();

-- ============================================================
-- 4. RLS POLICIES
-- ============================================================

-- users
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users: select for authenticated"
    ON public.users FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Users: update own profile"
    ON public.users FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = id)
    WITH CHECK ((select auth.uid()) = id);

-- tickets
ALTER TABLE public.tickets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tickets: select for authenticated"
    ON public.tickets FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Tickets: insert for authenticated"
    ON public.tickets FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) IS NOT NULL);

CREATE POLICY "Tickets: update for authenticated"
    ON public.tickets FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Tickets: delete for admin"
    ON public.tickets FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = (select auth.uid()) AND role = 'admin'
        )
    );

-- ticket_events_log
ALTER TABLE public.ticket_events_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Events: select for authenticated"
    ON public.ticket_events_log FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Events: insert for authenticated"
    ON public.ticket_events_log FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) IS NOT NULL);
