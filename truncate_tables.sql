-- Limpar tabelas completamente
TRUNCATE TABLE professionals CASCADE;
TRUNCATE TABLE procedures CASCADE;
TRUNCATE TABLE sync_log CASCADE;

-- Confirmar
SELECT COUNT(*) as professionals FROM professionals;
SELECT COUNT(*) as procedures FROM procedures;
SELECT COUNT(*) as sync_log FROM sync_log;
