"""
Script para verificar se o ambiente está configurado corretamente.

Execute este script após a instalação para garantir que tudo está ok.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Verifica versão do Python."""
    print("🔍 Verificando Python...")
    
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"   ❌ Python {version.major}.{version.minor} - Requer Python 3.8+")
        return False
    else:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True


def check_dependencies():
    """Verifica se dependências estão instaladas."""
    print("\n📦 Verificando dependências...")
    
    required = ['requests', 'pandas', 'tqdm', 'dotenv']
    all_ok = True
    
    for package in required:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} não encontrado")
            all_ok = False
    
    if not all_ok:
        print("\n   💡 Execute: pip install -r requirements.txt")
    
    return all_ok


def check_directories():
    """Verifica se diretórios necessários existem."""
    print("\n📁 Verificando diretórios...")
    
    required_dirs = ['cache', 'processed', 'logs', 'src/data_fetcher']
    all_ok = True
    
    for dir_name in required_dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️  {dir_name}/ não existe (será criado automaticamente)")
    
    return all_ok


def check_modules():
    """Verifica se módulos principais existem."""
    print("\n🔧 Verificando módulos...")
    
    required_files = [
        'src/data_fetcher/__init__.py',
        'src/data_fetcher/config.py',
        'src/data_fetcher/tmdb_client.py',
        'src/data_fetcher/movie_fetcher.py',
        'src/data_fetcher/validators.py',
        'src/data_fetcher/cache_manager.py',
        'src/data_fetcher/utils.py',
        'src/data_fetcher/main.py'
    ]
    
    all_ok = True
    
    for file_name in required_files:
        path = Path(file_name)
        if path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} não encontrado")
            all_ok = False
    
    return all_ok


def check_api_key():
    """Verifica se API key está configurada."""
    print("\n🔑 Verificando API key...")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("   ❌ Arquivo .env não encontrado")
        print("   💡 Execute: cp .env.example .env")
        return False
    
    # Tentar carregar
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('TMDB_API_KEY')
        
        if not api_key:
            print("   ⚠️  TMDB_API_KEY não definida no .env")
            print("   💡 Adicione sua chave em .env")
            return False
        elif api_key == 'your_api_key_here':
            print("   ⚠️  TMDB_API_KEY ainda é o valor exemplo")
            print("   💡 Substitua por sua chave real")
            return False
        else:
            # Ocultar parte da chave
            masked = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
            print(f"   ✅ TMDB_API_KEY configurada ({masked})")
            return True
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar: {e}")
        return False


def test_import():
    """Testa se módulos podem ser importados."""
    print("\n🧪 Testando imports...")
    
    try:
        from src.data_fetcher import TMDbDataPipeline
        print("   ✅ Módulos podem ser importados")
        return True
    except ImportError as e:
        print(f"   ❌ Erro ao importar: {e}")
        return False


def main():
    """Executa todas as verificações."""
    print("\n" + "=" * 60)
    print("TMDb Dataset Builder - Verificação de Setup")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Modules", check_modules),
        ("API Key", check_api_key),
        ("Import Test", test_import)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n   ❌ Erro durante verificação: {e}")
            results[name] = False
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ OK" if passed else "❌ FALHOU"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 Tudo configurado corretamente!")
        print("\n📝 Próximos passos:")
        print("   1. python example_usage.py")
        print("   2. python -m src.data_fetcher.main -i sample_movies.csv")
        print("\n📖 Veja QUICKSTART.md para mais informações\n")
    else:
        print("\n⚠️  Alguns problemas foram encontrados.")
        print("   Revise as mensagens acima e corrija os erros.")
        print("\n💡 Dicas:")
        print("   - Execute: pip install -r requirements.txt")
        print("   - Configure .env com sua API key")
        print("   - Veja QUICKSTART.md para ajuda\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())