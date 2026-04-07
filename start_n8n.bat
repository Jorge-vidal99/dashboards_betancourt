@echo off
title n8n - Transportes Betancourt
cd /d C:\Users\Pablo\Desktop\REPORTE

set N8N_ENABLE_EXECUTE_COMMAND=true
set NODES_INCLUDE=n8n-nodes-base.executeCommand
set N8N_BLOCK_ENV_ACCESS_IN_NODE=false
set NODE_FUNCTION_ALLOW_BUILTIN=child_process,fs,path
set N8N_RUNNERS_TASK_TIMEOUT=600

n8n start >> logs\n8n_startup.log 2>&1