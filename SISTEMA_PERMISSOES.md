# Sistema de Níveis de Permissão

## Visão Geral

Foi implementado um sistema completo de níveis de permissão no Ministério de Louvor, permitindo controle granular de acesso às funcionalidades do sistema.

## Níveis de Permissão

### 1. Admin (Administrador)
- **Acesso:** Total
- **Descrição:** Desenvolvedor/Administrador do sistema
- **Permissões:**
  - Gerenciar todos os membros (criar, editar, excluir, suspender)
  - Criar e gerenciar cultos
  - Criar e gerenciar escalas
  - Adicionar/remover músicas em qualquer escala
  - Gerenciar repertório completo
  - Acessar estatísticas e dashboard
  - Configurar períodos de indisponibilidade
  - Definir níveis de permissão de outros usuários

### 2. Pastor
- **Acesso:** Pleno (equivalente ao Admin, exceto gerenciamento de privilégios)
- **Descrição:** Pastor da igreja
- **Permissões:**
  - Todas as permissões do Admin
  - Gerenciar membros, cultos, escalas e músicas
  - Acessar todas as funcionalidades administrativas

### 3. Líder
- **Acesso:** Pleno (equivalente ao Pastor)
- **Descrição:** Líder do ministério de louvor
- **Permissões:**
  - Todas as permissões do Pastor
  - Gestão completa do ministério

### 4. Ministro de Louvor
- **Acesso:** Limitado (gerencia apenas suas escalas)
- **Descrição:** Ministro que participa das escalas
- **Permissões:**
  - Visualizar todas as escalas
  - **Adicionar/remover músicas APENAS das escalas em que está escalado**
  - Gerenciar seu próprio perfil
  - Registrar indisponibilidade
  - Visualizar repertório (sem editar)

### 5. Membro
- **Acesso:** Básico
- **Descrição:** Membro comum do ministério
- **Permissões:**
  - Visualizar suas próprias escalas
  - Gerenciar seu próprio perfil
  - Registrar indisponibilidade
  - Visualizar repertório (sem editar)

## Como Definir Níveis de Permissão

### Ao Criar um Novo Membro

1. Acesse a página **Membros**
2. Clique em **+ Novo Membro**
3. Preencha os dados do membro
4. No campo **Nível de Permissão**, selecione:
   - **Membro** (padrão)
   - **Ministro de Louvor**
   - **Líder**
   - **Pastor**
   - **Administrador**
5. Clique em **Salvar Membro**

### Ao Editar um Membro Existente

1. Acesse a página **Membros**
2. Clique no botão **Editar** do membro desejado
3. Altere o campo **Nível de Permissão**
4. Clique em **Atualizar**

## Regras Especiais

### Gerenciamento de Músicas em Escalas

- **Admin/Pastor/Líder:** Podem adicionar/remover músicas em **qualquer escala**
- **Ministro de Louvor:** Pode adicionar/remover músicas **APENAS nas escalas em que está escalado**
- **Membro:** **Não pode** gerenciar músicas

### Exemplo de Uso:

Se João é um **Ministro de Louvor** e está escalado como **Guitarrista** no culto de domingo às 10h:
- ✅ João PODE adicionar/remover músicas do culto de domingo às 10h
- ❌ João NÃO PODE adicionar/remover músicas de outros cultos

## Identificação Visual

Na página **Membros**, cada membro exibe um badge colorido indicando seu nível:

- 🔴 **Admin** (Vermelho)
- 🟣 **Pastor** (Roxo)
- 🔵 **Líder** (Azul)
- 🟠 **Ministro** (Laranja)
- ⚫ **Membro** (Cinza)

## Migração de Dados Existentes

Ao executar o script `migrate_add_roles.py`, todos os usuários e membros existentes foram atualizados:

- Usuários com `is_admin = True` → **Admin**
- Demais usuários/membros → **Membro**

Para ajustar os níveis, edite cada membro/usuário através da interface.

## Segurança

O sistema implementa verificações em **dois níveis**:

1. **Backend (app.py):**
   - Decoradores `@admin_required` e `@ministro_or_admin_required`
   - Função `can_manage_escala_musicas()` verifica permissões específicas
   - Verificações nas rotas `/add_musica_culto` e `/remove_musica_culto`

2. **Frontend (templates):**
   - Variáveis de contexto: `IS_ADMIN`, `IS_PASTOR`, `IS_LIDER`, `IS_MINISTRO`, `HAS_ADMIN_ACCESS`, `HAS_MINISTRO_ACCESS`
   - Botões e funcionalidades exibidos apenas para usuários autorizados

## Arquivos Modificados

- `app.py`: Modelos, decorators, rotas e context processor
- `templates/membros.html`: Interface de gerenciamento de permissões
- `templates/escalas.html`: Verificação de permissões para músicas
- `migrate_add_roles.py`: Script de migração do banco de dados

## Suporte

Para dúvidas ou problemas:
1. Verifique se o usuário tem o nível correto em **Membros**
2. Certifique-se de que executou o script de migração
3. Verifique os logs do servidor para mensagens de erro

---

**Desenvolvido por:** Sistema de Gerenciamento do Ministério de Louvor
**Data:** 13/03/2026
