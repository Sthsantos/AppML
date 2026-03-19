-- Migração: Adicionar colunas de confirmação à tabela escala
-- Execute este SQL no PostgreSQL do Render

-- 1. Adicionar coluna status_confirmacao
ALTER TABLE escala 
ADD COLUMN IF NOT EXISTS status_confirmacao VARCHAR(20) DEFAULT 'pendente';

-- 2. Adicionar coluna data_confirmacao  
ALTER TABLE escala
ADD COLUMN IF NOT EXISTS data_confirmacao TIMESTAMP NULL;

-- 3. Adicionar coluna observacao_confirmacao
ALTER TABLE escala
ADD COLUMN IF NOT EXISTS observacao_confirmacao TEXT NULL;

-- 4. Atualizar registros existentes com status pendente
UPDATE escala 
SET status_confirmacao = 'pendente' 
WHERE status_confirmacao IS NULL;

-- 5. Verificar se as colunas foram criadas (opcional)
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'escala' 
  AND column_name IN ('status_confirmacao', 'data_confirmacao', 'observacao_confirmacao')
ORDER BY column_name;

-- 6. Contar quantas escalas existem
SELECT COUNT(*) AS total_escalas FROM escala;
