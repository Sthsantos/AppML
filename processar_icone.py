"""
Script para processar o ícone: remove apenas o fundo preto externo,
mantém todo o desenho colorido intacto e amplia para preencher o espaço
"""
from PIL import Image
import os

# Caminho do ícone original
static_dir = os.path.join(os.path.dirname(__file__), 'static')
icon_path = os.path.join(static_dir, 'icon.png')

print(f"📁 Processando ícone: {icon_path}")

try:
    # Abrir a imagem
    img = Image.open(icon_path)
    print(f"✅ Imagem carregada: {img.size[0]}x{img.size[1]} pixels")
    
    # Converter para RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Criar uma nova imagem para processar
    pixels = img.load()
    width, height = img.size
    
    # Remover APENAS pixels pretos puros (fundo externo)
    # Usar threshold muito baixo para não remover partes do desenho
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            # Apenas pixels pretos puros (fundo externo)
            if r <= 10 and g <= 10 and b <= 10:
                pixels[x, y] = (0, 0, 0, 0)
    
    print("🧹 Removido fundo preto puro")
    
    # Encontrar a bounding box do conteúdo não-transparente
    bbox = img.getbbox()
    
    if bbox:
        print(f"📐 Área de conteúdo encontrada: {bbox}")
        
        # Fazer crop na área de conteúdo
        img_cropped = img.crop(bbox)
        
        # Calcular dimensões
        crop_width = bbox[2] - bbox[0]
        crop_height = bbox[3] - bbox[1]
        max_size = max(crop_width, crop_height)
        
        # Adicionar pequeno padding (5%) para não ficar colado nas bordas
        padding = int(max_size * 0.05)
        new_size = max_size + (padding * 2)
        
        # Criar imagem quadrada com transparência
        img_square = Image.new('RGBA', (new_size, new_size), (0, 0, 0, 0))
        
        # Calcular posição para centralizar
        paste_x = padding + (max_size - crop_width) // 2
        paste_y = padding + (max_size - crop_height) // 2
        
        # Colar a imagem cortada no centro
        img_square.paste(img_cropped, (paste_x, paste_y), img_cropped)
        
        # Redimensionar para 1024x1024 mantendo qualidade
        img_final = img_square.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        # Salvar o ícone processado
        img_final.save(icon_path, 'PNG', optimize=True, quality=95)
        print(f"✅ Ícone processado e salvo: 1024x1024 pixels")
        print("🎨 Fundo transparente com desenho completo ampliado")
        
    else:
        print("⚠️ Não foi possível encontrar conteúdo na imagem")
        
except Exception as e:
    print(f"❌ Erro: {str(e)}")
    exit(1)
