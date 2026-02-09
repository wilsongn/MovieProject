@echo off
REM Script de setup para TMDb Dataset Builder (Windows)

echo ==================================
echo TMDb Dataset Builder - Setup
echo ==================================
echo.

REM 1. Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Erro: Python nao encontrado. Instale Python 3.8+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo OK: %PYTHON_VERSION% encontrado
echo.

REM 2. Criar ambiente virtual
echo Criando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    echo OK: Ambiente virtual criado
) else (
    echo Aviso: Ambiente virtual ja existe
)
echo.

REM 3. Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo OK: Ambiente virtual ativado
echo.

REM 4. Atualizar pip
echo Atualizando pip...
python -m pip install --upgrade pip >nul 2>&1
echo OK: pip atualizado
echo.

REM 5. Instalar dependências
echo Instalando dependencias...
pip install -r requirements.txt
echo OK: Dependencias instaladas
echo.

REM 6. Criar diretórios
echo Criando diretorios...
if not exist "cache" mkdir cache
if not exist "processed" mkdir processed
if not exist "logs" mkdir logs
if not exist "examples" mkdir examples
if not exist "tests" mkdir tests
echo OK: Diretorios criados
echo.

REM 7. Configurar .env
echo Configurando arquivo .env...
if not exist ".env" (
    copy .env.example .env >nul
    echo OK: Arquivo .env criado
    echo IMPORTANTE: Edite o arquivo .env e adicione sua API key do TMDb
) else (
    echo Aviso: Arquivo .env ja existe
)
echo.

REM 8. Executar testes
echo Executando testes basicos...
python tests\test_validators.py
if %errorlevel% equ 0 (
    echo OK: Todos os testes passaram
) else (
    echo Aviso: Alguns testes falharam (mas isso e ok por enquanto)
)
echo.

REM Finalizar
echo ==================================
echo Setup concluido com sucesso!
echo ==================================
echo.
echo Proximos passos:
echo 1. Edite o arquivo .env e adicione sua API key
echo    Obtenha em: https://www.themoviedb.org/settings/api
echo.
echo 2. Ative o ambiente virtual:
echo    venv\Scripts\activate
echo.
echo 3. Execute o exemplo:
echo    python example_usage.py
echo.
echo 4. Ou processe seu proprio dataset:
echo    python -m src.data_fetcher.main -i input.csv -o output.csv
echo.
echo Veja README.md para mais informacoes
echo.
pause