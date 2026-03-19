# Persistência de Arquivos de Áudio no Render

## 🎯 Objetivo

Garantir que os arquivos de áudio do repertório não sejam perdidos após commits no GitHub e deploys no Render.

## 🚨 Problema

Por padrão, o sistema de arquivos do Render é **efêmero** - significa que qualquer arquivo salvo em `static/uploads` é perdido quando há um novo deploy.

## ✅ Solução: Render Disks

O Render oferece **Render Disks** - volumes persistentes que sobrevivem aos deploys.

---

## 📋 Passo a Passo - Configuração no Render

### 1. Criar um Render Disk

1. Acesse o **Dashboard do Render**: https://dashboard.render.com/
2. Vá no seu **Web Service** (AppML)
3. Clique na aba **"Disks"**
4. Clique em **"Add Disk"**
5. Configure:
   - **Name**: `audio-uploads`
   - **Mount Path**: `/var/data/uploads`
   - **Size**: 1 GB (ajuste conforme necessário)
6. Clique em **"Save Disk"**

### 2. Adicionar Variável de Ambiente

1. No Render Dashboard, vá em **"Environment"**
2. Adicione uma nova variável de ambiente:
   - **Key**: `PERSISTENT_UPLOAD_FOLDER`
   - **Value**: `/var/data/uploads`
3. Salve as alterações
4. O Render fará um **redeploy automático**

### 3. Migrar Arquivos Existentes (Opcional)

Se você já tem arquivos de áudio no sistema, precisará movê-los manualmente:

**Opção A - Via Render Shell:**
```bash
# Acesse o shell do seu serviço no Render Dashboard
# Em "Shell" (no menu lateral), execute:

mkdir -p /var/data/uploads
cp -r static/uploads/* /var/data/uploads/
```

**Opção B - Fazer novo upload:**
- Fazer upload novamente dos arquivos através do sistema

---

## 🔧 Como Funciona

O código detecta automaticamente se existe uma variável de ambiente `PERSISTENT_UPLOAD_FOLDER`:

```python
# app.py (já implementado)

# Detecta se há pasta persistente configurada (Render Disk)
persistent_folder = os.environ.get('PERSISTENT_UPLOAD_FOLDER')
if persistent_folder:
    app.config['UPLOAD_FOLDER'] = persistent_folder
    print(f"✅ Usando pasta persistente: {persistent_folder}")
else:
    # Desenvolvimento local
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    print(f"⚠️ Usando pasta local (não persistente): static/uploads")
```

### Fluxo:

1. **Desenvolvimento Local**: arquivos salvos em `static/uploads`
2. **Render (sem Disk)**: arquivos salvos em `static/uploads` (⚠️ perdem-se em cada deploy)
3. **Render (com Disk)**: arquivos salvos em `/var/data/uploads` (✅ persistem entre deploys)

---

## 📊 Custos

### Render Disks - Pricing

| Plano | Tamanho | Custo Mensal |
|-------|---------|--------------|
| Free | Não disponível | - |
| Individual | 1 GB | $0.25/GB/mês |
| Team/Business | 1 GB+ | $0.25/GB/mês |

**Exemplo:**
- 1 GB de armazenamento = **$0.25/mês**
- 5 GB de armazenamento = **$1.25/mês**

> 💡 **Dica**: 1 GB comporta aproximadamente 250 arquivos de áudio MP3 de 4 minutos cada (4 MB/música).

### Alternativas Gratuitas

Se quiser evitar custos, considere usar serviços gratuitos de armazenamento:

#### 1. **Cloudinary** (Recomendado para Imagens/Áudio)
- ✅ Plano gratuito: 25 GB de armazenamento
- ✅ 25 GB de bandwidth/mês
- ✅ API simples de integrar

#### 2. **AWS S3** (Mais complexo, mas escalável)
- ✅ 5 GB grátis no primeiro ano
- ⚠️ Requer configuração de IAM e credenciais

#### 3. **Supabase Storage** (PostgreSQL + Storage)
- ✅ 1 GB grátis
- ✅ Integração simples

---

## 🔐 Segurança

### Boas Práticas:

1. **Validação de arquivos**: ✅ Já implementado no código
   - Apenas extensões permitidas: MP3, WAV, OGG, M4A, AAC, FLAC
   - Limite de tamanho: 50 MB por arquivo

2. **Proteção contra sobrescrita**:
   - Nomes únicos gerados com timestamp

3. **Backup regular**:
   - Configure rotinas de backup do Render Disk
   - Ou sincronize periodicamente com S3/Cloudinary

---

## 🧪 Testando

### Verificar se está funcionando:

1. Faça upload de um arquivo de áudio
2. Faça um **deploy manual** ou commit no GitHub
3. Verifique se o arquivo ainda está disponível após o deploy
4. Teste o player de áudio

### Logs para verificar:

No Render Dashboard → **Logs**, procure por:
```
✅ Usando pasta persistente: /var/data/uploads
```

Ou (se ainda não configurou):
```
⚠️ Usando pasta local (não persistente): static/uploads
```

---

## 🆘 Solução de Problemas

### Problema: Arquivos ainda somem após deploy

**Causa**: Variável de ambiente não configurada ou Disk não montado

**Solução**:
1. Verifique nos **Environment Variables** se `PERSISTENT_UPLOAD_FOLDER` existe
2. Verifique na aba **Disks** se o disco está montado em `/var/data/uploads`
3. Faça um **Manual Deploy** após adicionar o Disk

### Problema: Erro de permissão ao salvar arquivo

**Causa**: Pasta não existe ou sem permissões de escrita

**Solução**:
```bash
# No Render Shell:
mkdir -p /var/data/uploads
chmod 755 /var/data/uploads
```

### Problema: Alto consumo de armazenamento

**Solução**:
- Limpar arquivos antigos/não utilizados
- Comprimir áudios antes do upload
- Aumentar tamanho do Disk (custo adicional)

---

## 📚 Referências

- [Render Disks Documentation](https://render.com/docs/disks)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Cloudinary Python SDK](https://cloudinary.com/documentation/python_integration)

---

## ✅ Checklist de Configuração

- [ ] Criar Render Disk `/var/data/uploads` (1 GB mínimo)
- [ ] Adicionar variável `PERSISTENT_UPLOAD_FOLDER=/var/data/uploads`
- [ ] Aguardar redeploy automático
- [ ] Verificar logs: "✅ Usando pasta persistente"
- [ ] Fazer upload de teste
- [ ] Fazer deploy manual e verificar persistência
- [ ] (Opcional) Migrar arquivos existentes
- [ ] Configurar backup regular

---

**Última atualização**: 19 de março de 2026
**Status**: ✅ Código já preparado para persistência
**Próximo passo**: Configurar Render Disk no dashboard
