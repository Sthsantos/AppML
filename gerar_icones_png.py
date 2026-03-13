#!/usr/bin/env python3
"""
Script para gerar ícones PNG a partir do SVG para compatibilidade iOS.
iOS não suporta SVG em apple-touch-icon, apenas PNG.
"""
import os
from pathlib import Path

def gerar_icones():
    """Gera ícones PNG a partir do SVG usando diferentes métodos."""
    
    print("🎨 Gerando ícones PNG para iOS...")
    
    # Tentar cairosvg primeiro (melhor qualidade)
    try:
        import cairosvg
        print("✅ Usando cairosvg (alta qualidade)")
        gerar_com_cairosvg()
        return
    except ImportError:
        print("⚠️  cairosvg não instalado")
    
    # Tentar PIL/Pillow
    try:
        from PIL import Image
        from io import BytesIO
        print("✅ Usando Pillow")
        gerar_com_pillow()
        return
    except ImportError:
        print("⚠️  Pillow não instalado")
    
    # Se nenhuma biblioteca disponível, instrui instalação
    print("\n❌ Nenhuma biblioteca de conversão disponível!")
    print("\n📦 Instale uma das seguintes opções:")
    print("   pip install cairosvg")
    print("   pip install Pillow wand")
    print("\nOu use um conversor online:")
    print("   https://convertio.co/pt/svg-png/")
    print("   https://cloudconvert.com/svg-to-png")
    print("\nTamanhos necessários: 180x180, 192x192, 512x512")


def gerar_com_cairosvg():
    """Gera PNGs usando cairosvg."""
    import cairosvg
    
    svg_path = Path(__file__).parent / 'static' / 'icon.svg'
    static_dir = Path(__file__).parent / 'static'
    
    tamanhos = [180, 192, 512]
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_data = f.read()
    
    for size in tamanhos:
        output_path = static_dir / f'icon-{size}x{size}.png'
        cairosvg.svg2png(
            bytestring=svg_data.encode('utf-8'),
            write_to=str(output_path),
            output_width=size,
            output_height=size
        )
        print(f"   ✓ Criado: icon-{size}x{size}.png")
    
    print(f"\n✅ {len(tamanhos)} ícones PNG gerados com sucesso!")


def gerar_com_pillow():
    """Gera PNGs usando Pillow + wand/ImageMagick."""
    try:
        from wand.image import Image as WandImage
        from PIL import Image
        
        svg_path = Path(__file__).parent / 'static' / 'icon.svg'
        static_dir = Path(__file__).parent / 'static'
        
        tamanhos = [180, 192, 512]
        
        for size in tamanhos:
            with WandImage(filename=str(svg_path)) as img:
                img.format = 'png'
                img.resize(size, size)
                output_path = static_dir / f'icon-{size}x{size}.png'
                img.save(filename=str(output_path))
                print(f"   ✓ Criado: icon-{size}x{size}.png")
        
        print(f"\n✅ {len(tamanhos)} ícones PNG gerados com sucesso!")
        
    except ImportError:
        print("❌ Wand não instalado. Tente: pip install Wand")
        print("   (Também requer ImageMagick instalado no sistema)")


if __name__ == '__main__':
    gerar_icones()
