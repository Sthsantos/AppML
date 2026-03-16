"""
Script para gerar ícones PWA a partir do icon.png na pasta static
"""
from PIL import Image
import os

# Caminho do ícone original
static_dir = os.path.join(os.path.dirname(__file__), 'static')
icon_path = os.path.join(static_dir, 'icon.png')

# Verificar se existe
if not os.path.exists(icon_path):
    print("❌ Erro: Não foi encontrado icon.png na pasta static")
    exit(1)

print(f"📁 Usando ícone: {icon_path}")

# Abrir a imagem original
try:
    img = Image.open(icon_path)
    print(f"✅ Imagem carregada: {img.size[0]}x{img.size[1]} pixels")
    
    # Converter para RGBA se necessário
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
        print("🔄 Convertido para RGBA")
    
    # Tamanhos necessários para PWA
    sizes = [192, 512, 180]
    
    for size in sizes:
        # Redimensionar mantendo qualidade
        icon_resized = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Salvar
        output_path = os.path.join(static_dir, f'icon-{size}x{size}.png')
        icon_resized.save(output_path, 'PNG', optimize=True, quality=95)
        print(f"✅ Criado: icon-{size}x{size}.png")
    
    print("\n🎉 Todos os ícones foram gerados com sucesso!")
    print("📱 Os ícones estão prontos para uso no PWA")
    
except Exception as e:
    print(f"❌ Erro ao processar imagem: {str(e)}")
    exit(1)
