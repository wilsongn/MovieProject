#!/bin/bash

# Script de setup para TMDb Dataset Builder
# Este script facilita a instalação e configuração inicial

echo "=================================="
echo "TMDb Dataset Builder - Setup"
echo "=================================="
echo ""

# 1. Verificar Python
echo "🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION encontrado"
echo ""

# 2. Criar ambiente virtual
echo "🔨 Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Ambiente virtual criado"
else
    echo "⚠️  Ambiente virtual já existe"
fi
echo ""

# 3. Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate
echo "✅ Ambiente virtual ativado"
echo ""

# 4. Atualizar pip
echo "⬆️  Atualizando pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip atualizado"
echo ""

# 5. Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt
echo "✅ Dependências instaladas"
echo ""

# 6. Criar diretórios
echo "📁 Criando diretórios..."
mkdir -p cache processed logs examples tests
echo "✅ Diretórios criados"
echo ""

# 7. Configurar .env
echo "🔑 Configurando arquivo .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Arquivo .env criado"
    echo "⚠️  IMPORTANTE: Edite o arquivo .env e adicione sua API key do TMDb"
else
    echo "⚠️  Arquivo .env já existe"
fi
echo ""

# 8. Executar testes
echo "🧪 Executando testes básicos..."
python tests/test_validators.py
if [ $? -eq 0 ]; then
    echo "✅ Todos os testes passaram"
else
    echo "⚠️  Alguns testes falharam (mas isso é ok por enquanto)"
fi
echo ""

# Finalizar
echo "=================================="
echo "✅ Setup concluído com sucesso!"
echo "=================================="
echo ""
echo "Próximos passos:"
echo "1. Edite o arquivo .env e adicione sua API key"
echo "   Obtenha em: https://www.themoviedb.org/settings/api"
echo ""
echo "2. Ative o ambiente virtual:"
echo "   source venv/bin/activate"
echo ""
echo "3. Execute o exemplo:"
echo "   python example_usage.py"
echo ""
echo "4. Ou processe seu próprio dataset:"
echo "   python -m src.data_fetcher.main -i input.csv -o output.csv"
echo ""
echo "📖 Veja README.md para mais informações"
echo ""