#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificação PWA
Testa se as rotas e arquivos PWA estão acessíveis
"""

import requests
import json
from colorama import init, Fore, Style

# Inicializar colorama
init(autoreset=True)

def test_pwa():
    """Testa funcionalidades PWA"""
    base_url = "http://127.0.0.1:5000"
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🔍 VERIFICAÇÃO PWA - Sistema Ministério de Louvor")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Teste 1: Service Worker
    print(f"{Fore.YELLOW}Teste 1: Service Worker (/sw.js)")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/sw.js", timeout=5)
        if response.status_code == 200:
            if 'serviceWorker' in response.text or 'self.addEventListener' in response.text:
                print(f"{Fore.GREEN}✅ Service Worker acessível e válido")
                print(f"{Fore.WHITE}   - Status: {response.status_code}")
                print(f"{Fore.WHITE}   - Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"{Fore.WHITE}   - Tamanho: {len(response.text)} bytes")
                tests_passed += 1
            else:
                print(f"{Fore.RED}❌ Service Worker acessível mas conteúdo inválido")
        else:
            print(f"{Fore.RED}❌ Service Worker não acessível (Status: {response.status_code})")
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao acessar Service Worker: {e}")
    
    print()
    
    # Teste 2: Manifest
    print(f"{Fore.YELLOW}Teste 2: Manifest (/manifest.json)")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/manifest.json", timeout=5)
        if response.status_code == 200:
            try:
                manifest = response.json()
                print(f"{Fore.GREEN}✅ Manifest acessível e válido")
                print(f"{Fore.WHITE}   - Status: {response.status_code}")
                print(f"{Fore.WHITE}   - Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"{Fore.WHITE}   - Nome: {manifest.get('name', 'N/A')}")
                print(f"{Fore.WHITE}   - Nome Curto: {manifest.get('short_name', 'N/A')}")
                print(f"{Fore.WHITE}   - Ícones: {len(manifest.get('icons', []))} definidos")
                print(f"{Fore.WHITE}   - Atalhos: {len(manifest.get('shortcuts', []))} definidos")
                tests_passed += 1
            except json.JSONDecodeError:
                print(f"{Fore.RED}❌ Manifest acessível mas JSON inválido")
        else:
            print(f"{Fore.RED}❌ Manifest não acessível (Status: {response.status_code})")
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao acessar Manifest: {e}")
    
    print()
    
    # Teste 3: Página Principal
    print(f"{Fore.YELLOW}Teste 3: Página Principal (/)")
    tests_total += 1
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            html = response.text
            has_manifest = '<link rel="manifest"' in html
            has_service_worker = 'serviceWorker.register' in html
            has_pwa_meta = 'theme-color' in html or 'apple-mobile-web-app' in html
            
            if has_manifest and has_service_worker and has_pwa_meta:
                print(f"{Fore.GREEN}✅ Página principal com recursos PWA")
                print(f"{Fore.WHITE}   - Manifest link: {'✅' if has_manifest else '❌'}")
                print(f"{Fore.WHITE}   - Service Worker registration: {'✅' if has_service_worker else '❌'}")
                print(f"{Fore.WHITE}   - Meta tags PWA: {'✅' if has_pwa_meta else '❌'}")
                tests_passed += 1
            else:
                print(f"{Fore.RED}❌ Página acessível mas faltam recursos PWA")
                print(f"{Fore.WHITE}   - Manifest link: {'✅' if has_manifest else '❌'}")
                print(f"{Fore.WHITE}   - Service Worker registration: {'✅' if has_service_worker else '❌'}")
                print(f"{Fore.WHITE}   - Meta tags PWA: {'✅' if has_pwa_meta else '❌'}")
        else:
            print(f"{Fore.RED}❌ Página não acessível (Status: {response.status_code})")
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao acessar página principal: {e}")
    
    print()
    
    # Teste 4: Servidor Online
    print(f"{Fore.YELLOW}Teste 4: Servidor Flask")
    tests_total += 1
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code in [200, 302, 401]:  # 200 OK, 302 Redirect, 401 Unauthorized são válidos
            print(f"{Fore.GREEN}✅ Servidor Flask rodando")
            print(f"{Fore.WHITE}   - URL: {base_url}")
            print(f"{Fore.WHITE}   - Status: {response.status_code}")
            tests_passed += 1
        else:
            print(f"{Fore.RED}❌ Servidor retornou status inesperado: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Servidor não está rodando em {base_url}")
        print(f"{Fore.YELLOW}   💡 Execute: python app.py")
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao conectar ao servidor: {e}")
    
    # Resultado Final
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}📊 RESULTADO FINAL")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    percentage = (tests_passed / tests_total) * 100 if tests_total > 0 else 0
    
    if tests_passed == tests_total:
        color = Fore.GREEN
        status = "🎉 TODOS OS TESTES PASSARAM!"
    elif tests_passed >= tests_total * 0.75:
        color = Fore.YELLOW
        status = "⚠️ MAIORIA DOS TESTES PASSOU"
    else:
        color = Fore.RED
        status = "❌ VÁRIOS TESTES FALHARAM"
    
    print(f"{color}{status}")
    print(f"{Fore.WHITE}Testes Passados: {tests_passed}/{tests_total} ({percentage:.0f}%)\n")
    
    if tests_passed == tests_total:
        print(f"{Fore.GREEN}✅ Sistema PWA está 100% funcional!")
        print(f"{Fore.WHITE}")
        print(f"🚀 PRÓXIMOS PASSOS:")
        print(f"   1. Acesse: {base_url}")
        print(f"   2. Aguarde 3 segundos")
        print(f"   3. Banner de instalação aparecerá")
        print(f"   4. Ou abra DevTools (F12) e veja:")
        print(f"      - Console: '✅ Service Worker registrado'")
        print(f"      - Application → Service Workers: 'activated'")
        print(f"      - Application → Manifest: Dados do app")
    else:
        print(f"{Fore.YELLOW}💡 AÇÕES RECOMENDADAS:")
        if tests_passed < tests_total:
            print(f"{Fore.WHITE}   1. Verifique se o servidor está rodando: python app.py")
            print(f"   2. Confirme que as rotas PWA estão em app.py")
            print(f"   3. Verifique arquivos: static/sw.js e static/manifest.json")
            print(f"   4. Reinicie o servidor: Ctrl+C e python app.py")
    
    print(f"\n{Fore.CYAN}{'='*60}\n")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    try:
        success = test_pwa()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️ Teste interrompido pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Erro inesperado: {e}")
        exit(1)
