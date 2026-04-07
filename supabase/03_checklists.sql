-- ============================================================
-- 5. TABELA: ticket_checklists (Sub-tarefas dentro de um ticket)
-- ============================================================
CREATE TABLE public.ticket_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT false,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_checklists_ticket ON public.ticket_checklists(ticket_id);

-- RLS POLICIES
ALTER TABLE public.ticket_checklists ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Checklists: select for authenticated"
    ON public.ticket_checklists FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Checklists: insert for authenticated"
    ON public.ticket_checklists FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) IS NOT NULL);

CREATE POLICY "Checklists: update for authenticated"
    ON public.ticket_checklists FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Checklists: delete for authenticated"
    ON public.ticket_checklists FOR DELETE
    TO authenticated
    USING (true);
