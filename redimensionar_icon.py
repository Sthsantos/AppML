#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para redimensionar icon.png para os tamanhos necessários do PWA
"""

from PIL import Image
import os

# Tamanhos necessários
tamanhos = [180, 192, 512]

# Abrir a imagem original
try:
    img_original = Image.open('static/icon.png')
    print(f"✅ Imagem original carregada: {img_original.size}")
    
    # Converter para RGBA se necessário (para manter transparência)
    if img_original.mode != 'RGBA':
        img_original = img_original.convert('RGBA')
    
    # Gerar cada tamanho
    for tamanho in tamanhos:
        # Redimensionar mantendo qualidade
        img_redimensionada = img_original.resize((tamanho, tamanho), Image.Resampling.LANCZOS)
        
        # Salvar
        nome_arquivo = f'static/icon-{tamanho}x{tamanho}.png'
        img_redimensionada.save(nome_arquivo, 'PNG', optimize=True)
        
        print(f"   ✓ Criado: icon-{tamanho}x{tamanho}.png")
    
    print(f"\n✅ {len(tamanhos)} ícones PNG gerados com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    print("\nTentando instalar Pillow...")
    import subprocess
    subprocess.run(['pip', 'install', 'pillow'])
