-- ============================================================
-- Migração #2: Participantes Múltiplos, Anexos e Storage Buckets
-- Execute no SQL Editor do seu projeto Supabase
-- ============================================================

-- 1. [OPCIONAL] Remove fallback de assignee (Caso opte por usar apenas a Lista de Participantes)
-- NOTA: O painel atual mantém a semântica do 'assignee_id' como "Dono" da tarefa.
-- Esta tabela gerencia os EXTRAS (Convidados).

CREATE TABLE IF NOT EXISTS public.ticket_participants (
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ticket_id, user_id)
);

CREATE POLICY "Participantes: todos authenticated podem ler"
    ON public.ticket_participants FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Participantes: todos authenticated podem alterar"
    ON public.ticket_participants FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

ALTER TABLE public.ticket_participants ENABLE ROW LEVEL SECURITY;

-- 2. Tabela para referenciar anexos inseridos nos tasks
CREATE TABLE IF NOT EXISTS public.ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    uploaded_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE POLICY "Anexos: ler"
    ON public.ticket_attachments FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Anexos: inserir"
    ON public.ticket_attachments FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) IS NOT NULL);

CREATE POLICY "Anexos: deletar"
    ON public.ticket_attachments FOR DELETE
    TO authenticated
    USING ((select auth.uid()) = uploaded_by OR EXISTS (
        SELECT 1 FROM public.users WHERE id = (select auth.uid()) AND role = 'admin'
    ));

ALTER TABLE public.ticket_attachments ENABLE ROW LEVEL SECURITY;

-- 3. Criação do Bucket de Storage (via RPC interna do Supabase se o banco for superuser)
-- Isso cria o bucket se ele não existir
INSERT INTO storage.buckets (id, name, public) 
VALUES ('tickets-attachments', 'tickets-attachments', true)
ON CONFLICT (id) DO NOTHING;

-- 4. Storage Policies para permitir que usuários autenticados façam upload
CREATE POLICY "Permite leitura publica dos anexos"
    ON storage.objects FOR SELECT
    TO public
    USING ( bucket_id = 'tickets-attachments' );

CREATE POLICY "Permite inserção autenticada nos anexos"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK ( bucket_id = 'tickets-attachments' );

CREATE POLICY "Permite update pelo dono nos anexos"
    ON storage.objects FOR UPDATE
    TO authenticated
    USING ( bucket_id = 'tickets-attachments' AND auth.uid() = owner )
    WITH CHECK ( bucket_id = 'tickets-attachments' );

CREATE POLICY "Permite exclusão pelo dono nos anexos"
    ON storage.objects FOR DELETE
    TO authenticated
    USING ( bucket_id = 'tickets-attachments' AND auth.uid() = owner );
