#!/usr/bin/env python3
"""Verifica avisos criados recentemente."""
from app import app, db, Aviso
from datetime import datetime, timedelta

def verificar_avisos():
    with app.app_context():
        print("\n" + "="*50)
        print("  AVISOS RECENTES")
        print("="*50 + "\n")
        
        # Últimos 5 avisos
        avisos = Aviso.query.order_by(Aviso.created_at.desc()).limit(5).all()
        
        if not avisos:
            print("❌ Nenhum aviso encontrado no banco!\n")
            return
        
        print(f"📊 Total de avisos no banco: {Aviso.query.count()}")
        print(f"\n📋 Últimos 5 avisos:\n")
        
        for idx, aviso in enumerate(avisos, 1):
            print(f"{idx}. [{aviso.priority.upper()}] {aviso.title}")
            print(f"   Mensagem: {aviso.message[:60]}...")
            print(f"   Criado em: {aviso.created_at}")
            print(f"   Ativo: {'✅' if aviso.active else '❌'}")
            print()
        
        print("="*50 + "\n")

if __name__ == '__main__':
    verificar_avisos()
