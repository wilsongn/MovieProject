"""
Testes unitários para o módulo validators.py
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher.validators import MovieValidator


def test_valid_movie():
    """Testa filme com dados válidos."""
    validator = MovieValidator()
    
    movie = {
        'tmdb_id': 12345,
        'title': 'Test Movie',
        'overview': 'This is a test movie with enough characters in the overview.',
        'release_date': '2023-01-01',
        'year': 2023,
        'genres': ['Action', 'Drama']
    }
    
    is_valid, error = validator.validate_movie(movie)
    
    assert is_valid == True, f"Deveria ser válido: {error}"
    assert error == "", "Não deveria ter mensagem de erro"
    print("✅ test_valid_movie passou")


def test_missing_required_field():
    """Testa filme sem campo obrigatório."""
    validator = MovieValidator()
    
    movie = {
        'tmdb_id': 12345,
        'title': 'Test Movie',
        # overview faltando!
        'release_date': '2023-01-01',
        'year': 2023,
        'genres': ['Action']
    }
    
    is_valid, error = validator.validate_movie(movie)
    
    assert is_valid == False, "Deveria ser inválido"
    assert "overview" in error.lower(), "Erro deveria mencionar overview"
    print("✅ test_missing_required_field passou")


def test_short_overview():
    """Testa filme com sinopse muito curta."""
    validator = MovieValidator()
    
    movie = {
        'tmdb_id': 12345,
        'title': 'Test Movie',
        'overview': 'Too short',  # Menos de 20 caracteres
        'release_date': '2023-01-01',
        'year': 2023,
        'genres': ['Action']
    }
    
    is_valid, error = validator.validate_movie(movie)
    
    assert is_valid == False, "Deveria ser inválido"
    assert "curto" in error.lower() or "short" in error.lower(), \
        "Erro deveria mencionar overview curto"
    print("✅ test_short_overview passou")


def test_invalid_year():
    """Testa filme com ano inválido."""
    validator = MovieValidator()
    
    movie = {
        'tmdb_id': 12345,
        'title': 'Test Movie',
        'overview': 'This is a test movie with enough characters.',
        'release_date': '1800-01-01',
        'year': 1800,  # Antes de 1888
        'genres': ['Action']
    }
    
    is_valid, error = validator.validate_movie(movie)
    
    assert is_valid == False, "Deveria ser inválido"
    assert "ano" in error.lower() or "year" in error.lower(), \
        "Erro deveria mencionar ano"
    print("✅ test_invalid_year passou")


def test_no_genres():
    """Testa filme sem gêneros."""
    validator = MovieValidator()
    
    movie = {
        'tmdb_id': 12345,
        'title': 'Test Movie',
        'overview': 'This is a test movie with enough characters.',
        'release_date': '2023-01-01',
        'year': 2023,
        'genres': []  # Lista vazia
    }
    
    is_valid, error = validator.validate_movie(movie)
    
    assert is_valid == False, "Deveria ser inválido"
    assert "gênero" in error.lower() or "genre" in error.lower(), \
        "Erro deveria mencionar gêneros"
    print("✅ test_no_genres passou")


def test_is_valid_tmdb_id():
    """Testa validação de TMDb ID."""
    validator = MovieValidator()
    
    assert validator.is_valid_tmdb_id(12345) == True
    assert validator.is_valid_tmdb_id("12345") == True
    assert validator.is_valid_tmdb_id(-1) == False
    assert validator.is_valid_tmdb_id(0) == False
    assert validator.is_valid_tmdb_id("invalid") == False
    assert validator.is_valid_tmdb_id(None) == False
    
    print("✅ test_is_valid_tmdb_id passou")


def test_is_valid_year():
    """Testa validação de ano."""
    validator = MovieValidator()
    
    assert validator.is_valid_year(2023) == True
    assert validator.is_valid_year("2023") == True
    assert validator.is_valid_year(1950) == True
    assert validator.is_valid_year(1800) == False
    assert validator.is_valid_year(2050) == False
    assert validator.is_valid_year("invalid") == False
    assert validator.is_valid_year(None) == False
    
    print("✅ test_is_valid_year passou")


def test_sanitize_text():
    """Testa sanitização de texto."""
    validator = MovieValidator()
    
    # Quebras de linha
    text = "Line 1\nLine 2\rLine 3"
    sanitized = validator.sanitize_text(text)
    assert "\n" not in sanitized
    assert "\r" not in sanitized
    
    # Múltiplos espaços
    text = "Too   many    spaces"
    sanitized = validator.sanitize_text(text)
    assert "  " not in sanitized
    
    # Aspas duplas
    text = 'He said "hello"'
    sanitized = validator.sanitize_text(text)
    assert '"' not in sanitized
    
    print("✅ test_sanitize_text passou")


def run_all_tests():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("Executando testes de validators.py")
    print("=" * 60 + "\n")
    
    tests = [
        test_valid_movie,
        test_missing_required_field,
        test_short_overview,
        test_invalid_year,
        test_no_genres,
        test_is_valid_tmdb_id,
        test_is_valid_year,
        test_sanitize_text
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} falhou: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} erro: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Resultados: {passed} passou, {failed} falhou")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)