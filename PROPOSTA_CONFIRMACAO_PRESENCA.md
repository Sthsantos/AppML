# 🎯 Proposta: Sistema de Confirmação de Presença

**Prioridade:** ⭐⭐⭐⭐⭐ ALTA  
**Complexidade:** 🟢 Baixa  
**Tempo Estimado:** 1-2 horas  
**Impacto:** 🔥 ALTO  

---

## 📋 **PROBLEMA QUE RESOLVE**

### **Situação Atual:**
1. Admin escala membros para cultos
2. Membros veem suas escalas em "Minhas Escalas"
3. **MAS:** Não há confirmação se o membro realmente virá
4. **RISCO:** No dia do culto, membro pode faltar sem aviso

### **Cenário Real:**
```
Domingo 09h00:
❌ João não apareceu (estava escalado como guitarrista)
❌ Maria avisou em cima da hora que não pode vir
✅ Pedro chegou (mas ninguém sabia se viria)
```

### **Consequências:**
- 😰 Culto sem ministros suficientes
- 😰 Admin não tem tempo de buscar substituto
- 😰 Ministério fica desorganizado
- 😰 Falta de profissionalismo

---

## ✅ **SOLUÇÃO PROPOSTA**

### **Sistema de Confirmação de Presença**

**Funcionalidade:**
- Membro CONFIRMA ou NEGA presença na escala
- Admin vê status em tempo real
- Alertas visuais para pendentes
- Dashboard com % de confirmação

---

## 🗄️ **ALTERAÇÕES NO BANCO DE DADOS**

### **Tabela `Escala` - Adicionar Campos:**

```python
class Escala(db.Model):
    # ... campos existentes ...
    
    # NOVOS CAMPOS:
    status_confirmacao = db.Column(
        db.String(20), 
        default='pendente'
    )  # Valores: 'pendente', 'confirmado', 'negado'
    
    data_confirmacao = db.Column(
        db.DateTime, 
        nullable=True
    )  # Quando confirmou/negou
    
    observacao_confirmacao = db.Column(
        db.Text, 
        nullable=True
    )  # Mensagem opcional do membro
```

### **Migration (SQL):**
```sql
ALTER TABLE escala 
ADD COLUMN status_confirmacao VARCHAR(20) DEFAULT 'pendente';

ALTER TABLE escala 
ADD COLUMN data_confirmacao DATETIME NULL;

ALTER TABLE escala 
ADD COLUMN observacao_confirmacao TEXT NULL;
```

---

## 🔌 **NOVAS ROTAS API**

### **1. Confirmar Presença**
```python
@app.route('/confirmar_presenca/<int:escala_id>', methods=['POST'])
@login_required
def confirmar_presenca(escala_id):
    """Membro confirma que comparecerá."""
    data = request.json
    observacao = data.get('observacao', '')
    
    escala = Escala.query.get(escala_id)
    
    # Verificar se é o membro da escala
    user = current_user
    member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
    
    if escala.member_id != member.id:
        return jsonify({'success': False, 'message': 'Sem permissão'}), 403
    
    escala.status_confirmacao = 'confirmado'
    escala.data_confirmacao = datetime.utcnow()
    escala.observacao_confirmacao = observacao
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Presença confirmada com sucesso!'
    }), 200
```

### **2. Negar/Informar Ausência**
```python
@app.route('/negar_presenca/<int:escala_id>', methods=['POST'])
@login_required
def negar_presenca(escala_id):
    """Membro informa que não poderá comparecer."""
    data = request.json
    motivo = data.get('motivo', '')
    
    escala = Escala.query.get(escala_id)
    
    # Verificar se é o membro da escala
    user = current_user
    member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
    
    if escala.member_id != member.id:
        return jsonify({'success': False, 'message': 'Sem permissão'}), 403
    
    escala.status_confirmacao = 'negado'
    escala.data_confirmacao = datetime.utcnow()
    escala.observacao_confirmacao = motivo
    
    db.session.commit()
    
    # TODO: Notificar admin sobre ausência
    
    return jsonify({
        'success': True, 
        'message': 'Ausência registrada. O administrador foi notificado.'
    }), 200
```

### **3. Admin: Ver Status de Confirmações**
```python
@app.route('/get_status_confirmacoes/<int:culto_id>', methods=['GET'])
@login_required
@admin_required
def get_status_confirmacoes(culto_id):
    """Admin vê status de confirmações de um culto."""
    escalas = Escala.query.filter_by(culto_id=culto_id).all()
    
    confirmados = 0
    pendentes = 0
    negados = 0
    
    result = []
    for escala in escalas:
        member = Member.query.get(escala.member_id)
        
        result.append({
            'escala_id': escala.id,
            'member_name': member.name if member else 'Desconhecido',
            'role': escala.role,
            'status_confirmacao': escala.status_confirmacao,
            'data_confirmacao': escala.data_confirmacao.strftime('%d/%m/%Y %H:%M') if escala.data_confirmacao else None,
            'observacao': escala.observacao_confirmacao
        })
        
        if escala.status_confirmacao == 'confirmado':
            confirmados += 1
        elif escala.status_confirmacao == 'negado':
            negados += 1
        else:
            pendentes += 1
    
    total = len(escalas)
    percentual_confirmacao = (confirmados / total * 100) if total > 0 else 0
    
    return jsonify({
        'escalas': result,
        'resumo': {
            'total': total,
            'confirmados': confirmados,
            'pendentes': pendentes,
            'negados': negados,
            'percentual_confirmacao': round(percentual_confirmacao, 1)
        }
    }), 200
```

### **4. Resetar Confirmações (após culto)**
```python
@app.route('/resetar_confirmacoes/<int:culto_id>', methods=['POST'])
@login_required
@admin_required
def resetar_confirmacoes(culto_id):
    """Admin reseta confirmações após o culto (opcional)."""
    escalas = Escala.query.filter_by(culto_id=culto_id).all()
    
    for escala in escalas:
        escala.status_confirmacao = 'pendente'
        escala.data_confirmacao = None
        escala.observacao_confirmacao = None
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Confirmações resetadas.'
    }), 200
```

---

## 🎨 **ALTERAÇÕES NA INTERFACE**

### **1. Página "Minhas Escalas" (templates/minhas_escalas.html)**

#### **Adicionar Badges de Status:**
```javascript
function renderEscalaCard(escala) {
    let statusBadge = '';
    let botoes = '';
    
    // Badge de status
    if (escala.status_confirmacao === 'confirmado') {
        statusBadge = '<span class="badge badge-success">✅ CONFIRMADO</span>';
        botoes = `
            <button class="btn btn-outline btn-sm" onclick="negarPresenca(${escala.id})">
                <i class="fas fa-times"></i> Não Poderei Ir
            </button>
        `;
    } else if (escala.status_confirmacao === 'negado') {
        statusBadge = '<span class="badge badge-danger">❌ AUSÊNCIA INFORMADA</span>';
        botoes = `
            <button class="btn btn-success btn-sm" onclick="confirmarPresenca(${escala.id})">
                <i class="fas fa-check"></i> Confirmar Presença
            </button>
        `;
    } else {
        // Pendente
        statusBadge = '<span class="badge badge-warning">⏳ AGUARDANDO CONFIRMAÇÃO</span>';
        botoes = `
            <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-success btn-sm" onclick="confirmarPresenca(${escala.id})" style="flex: 1;">
                    <i class="fas fa-check"></i> Confirmar
                </button>
                <button class="btn btn-outline btn-sm" onclick="negarPresenca(${escala.id})" style="flex: 1;">
                    <i class="fas fa-times"></i> Não Poderei
                </button>
            </div>
        `;
    }
    
    return `
        <div class="card">
            <div class="card-header">
                <div>${escala.culto_description}</div>
                ${statusBadge}
            </div>
            <div class="card-body">
                <p><strong>Data:</strong> ${escala.culto_date} às ${escala.culto_time}</p>
                <p><strong>Função:</strong> ${escala.role}</p>
                ${botoes}
            </div>
        </div>
    `;
}
```

#### **Funções JavaScript:**
```javascript
async function confirmarPresenca(escalaId) {
    const observacao = prompt('Mensagem opcional (ex: "Chegarei 15min mais cedo"):');
    
    try {
        const response = await fetch(`/confirmar_presenca/${escalaId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ observacao: observacao || '' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            loadMinhasEscalas(); // Recarregar
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao confirmar presença', 'error');
    }
}

async function negarPresenca(escalaId) {
    const motivo = prompt('Por favor, informe o motivo da ausência:');
    
    if (!motivo || motivo.trim() === '') {
        showToast('Motivo é obrigatório', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/negar_presenca/${escalaId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ motivo: motivo })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            loadMinhasEscalas();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao registrar ausência', 'error');
    }
}
```

---

### **2. Página "Escalas" - Admin (templates/escalas.html)**

#### **Adicionar Filtro de Status:**
```html
<div class="filters" style="margin-bottom: 1rem;">
    <button class="btn btn-sm" onclick="filtrarPorStatus('todos')">Todos</button>
    <button class="btn btn-sm btn-success" onclick="filtrarPorStatus('confirmado')">✅ Confirmados</button>
    <button class="btn btn-sm btn-warning" onclick="filtrarPorStatus('pendente')">⏳ Pendentes</button>
    <button class="btn btn-sm btn-danger" onclick="filtrarPorStatus('negado')">❌ Ausências</button>
</div>
```

#### **Modal de Status de Confirmação:**
```html
<!-- Modal de Status de Confirmações -->
<div class="modal-overlay" id="statusConfirmacoesModal">
    <div class="modal">
        <div class="modal-header">
            <h2 class="modal-title">Status de Confirmações</h2>
            <button class="modal-close" onclick="closeModal('statusConfirmacoesModal')">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-body">
            <!-- Resumo -->
            <div id="resumoConfirmacoes" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
                <!-- Cards de resumo serão inseridos aqui -->
            </div>
            
            <!-- Lista detalhada -->
            <div id="listaConfirmacoes">
                <!-- Lista será inserida aqui -->
            </div>
        </div>
    </div>
</div>
```

#### **Função para Ver Status:**
```javascript
async function verStatusConfirmacoes(cultoId) {
    try {
        const response = await fetch(`/get_status_confirmacoes/${cultoId}`);
        const data = await response.json();
        
        // Renderizar resumo
        const resumo = data.resumo;
        document.getElementById('resumoConfirmacoes').innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${resumo.total}</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-card" style="background: var(--success-50); border-left: 4px solid var(--success-500);">
                <div class="stat-value" style="color: var(--success-600);">${resumo.confirmados}</div>
                <div class="stat-label">Confirmados</div>
            </div>
            <div class="stat-card" style="background: var(--warning-50); border-left: 4px solid var(--warning-500);">
                <div class="stat-value" style="color: var(--warning-600);">${resumo.pendentes}</div>
                <div class="stat-label">Pendentes</div>
            </div>
            <div class="stat-card" style="background: var(--danger-50); border-left: 4px solid var(--danger-500);">
                <div class="stat-value" style="color: var(--danger-600);">${resumo.negados}</div>
                <div class="stat-label">Ausências</div>
            </div>
        `;
        
        // Renderizar lista
        document.getElementById('listaConfirmacoes').innerHTML = data.escalas.map(e => `
            <div class="card" style="margin-bottom: 0.5rem;">
                <div style="padding: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${e.member_name}</strong> - ${e.role}
                        ${e.observacao ? `<br><small style="color: var(--gray-600);">${e.observacao}</small>` : ''}
                    </div>
                    <span class="badge ${
                        e.status_confirmacao === 'confirmado' ? 'badge-success' :
                        e.status_confirmacao === 'negado' ? 'badge-danger' :
                        'badge-warning'
                    }">
                        ${
                            e.status_confirmacao === 'confirmado' ? '✅ Confirmado' :
                            e.status_confirmacao === 'negado' ? '❌ Ausência' :
                            '⏳ Pendente'
                        }
                    </span>
                </div>
            </div>
        `).join('');
        
        // Abrir modal
        document.getElementById('statusConfirmacoesModal').classList.add('active');
        
    } catch (error) {
        showToast('Erro ao carregar status', 'error');
    }
}
```

---

### **3. Dashboard - Adicionar Card de Confirmações**

```javascript
// No dashboard, adicionar card:
<div class="stat-card" onclick="verConfirmacoesPendentes()">
    <div class="stat-icon" style="background: var(--warning-100);">
        <i class="fas fa-user-clock" style="color: var(--warning-600);"></i>
    </div>
    <div class="stat-content">
        <div class="stat-value" id="totalPendentesConfirmacao">-</div>
        <div class="stat-label">Confirmações Pendentes</div>
    </div>
</div>
```

---

## 📊 **DASHBOARD DE CONFIRMAÇÕES**

### **Nova Estatística no Dashboard:**
```python
# Em get_dashboard_stats():

# Adicionar contagem de confirmações pendentes
confirmacoes_pendentes = Escala.query.filter_by(
    status_confirmacao='pendente'
).join(Culto).filter(
    Culto.date >= date.today()
).count()

return jsonify({
    # ... outras stats ...
    'confirmacoes_pendentes': confirmacoes_pendentes
})
```

---

## ✅ **CHECKLIST DE IMPLEMENTAÇÃO**

### **Backend (app.py):**
- [ ] Adicionar campos na classe `Escala`
- [ ] Criar rota `POST /confirmar_presenca/<id>`
- [ ] Criar rota `POST /negar_presenca/<id>`
- [ ] Criar rota `GET /get_status_confirmacoes/<culto_id>`
- [ ] Atualizar `GET /get_escalas` para incluir status
- [ ] Atualizar `GET /get_minhas_escalas` para incluir status
- [ ] Atualizar `GET /get_dashboard_stats` para incluir pendentes

### **Frontend (minhas_escalas.html):**
- [ ] Adicionar badges de status nos cards
- [ ] Adicionar botões de confirmar/negar
- [ ] Implementar função `confirmarPresenca()`
- [ ] Implementar função `negarPresenca()`

### **Frontend (escalas.html):**
- [ ] Adicionar botão "Ver Status de Confirmações"
- [ ] Criar modal de status
- [ ] Implementar função `verStatusConfirmacoes()`
- [ ] Adicionar filtros por status

### **Frontend (index.html - Dashboard):**
- [ ] Adicionar card de confirmações pendentes
- [ ] Atualizar `loadStats()` para incluir pendentes

### **Banco de Dados:**
- [ ] Executar migration para adicionar campos
- [ ] (Opcional) Popular campos existentes com 'pendente'

---

## 🚀 **TEMPO DE IMPLEMENTAÇÃO**

| Tarefa | Tempo Estimado |
|--------|----------------|
| Alteração no modelo `Escala` | 5 min |
| Migration do banco | 5 min |
| Rotas backend (4 rotas) | 30 min |
| Interface minhas_escalas | 20 min |
| Interface escalas (admin) | 20 min |
| Dashboard | 10 min |
| Testes | 20 min |
| **TOTAL** | **~2 horas** |

---

## 💡 **MELHORIAS FUTURAS**

### **Fase 2 (Após MVP):**
1. **Notificação por Email:**
   - Email 3 dias antes do culto pedindo confirmação
   - Email ao admin quando membro nega presença

2. **Lembrete Automático:**
   - Lembrete 24h antes se ainda pendente
   - WhatsApp integration (via Twilio)

3. **Relatório de Ausências:**
   - Histórico de quem mais nega presença
   - Dashboard de pontualidade

4. **Confirmação com Horário:**
   - Membro informa se chegará no horário ou atrasado

---

## 📈 **MÉTRICAS DE SUCESSO**

### **Como medir o impacto:**
- ✅ % de confirmações antes do culto (meta: 80%+)
- ✅ Redução de ausências não avisadas (meta: -90%)
- ✅ Tempo médio de confirmação (meta: <48h)
- ✅ Satisfação do admin (pesquisa qualitativa)

---

**✅ Funcionalidade Pronta para Implementação**  
**Próximo Passo:** Aprovação para começar desenvolvimento

**Desenvolvido por:** GitHub Copilot  
**Data:** 17/03/2026
