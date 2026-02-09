"""
Exemplos de uso do TMDb Dataset Builder.

Execute este arquivo para ver o sistema em ação.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Importar nosso pipeline
from src.data_fetcher import TMDbDataPipeline
from src.data_fetcher import utils


def example_1_single_movie():
    """Exemplo 1: Buscar dados de um único filme."""
    print("\n" + "=" * 60)
    print("EXEMPLO 1: Buscar dados de um único filme")
    print("=" * 60)
    
    # Carregar API key
    load_dotenv()
    api_key = os.getenv('TMDB_API_KEY')
    
    if not api_key:
        print("❌ API key não encontrada. Configure no arquivo .env")
        return
    
    # Inicializar pipeline
    pipeline = TMDbDataPipeline(api_key=api_key)
    
    # Buscar filme
    print("\n🔍 Buscando: Inception (2010)...")
    movie = pipeline.process_single_movie(title="Inception", year=2010)
    
    if movie:
        print("\n✅ Filme encontrado!")
        print(f"ID: {movie['tmdb_id']}")
        print(f"Título: {movie['title']}")
        print(f"Ano: {movie['year']}")
        print(f"Gêneros: {', '.join(movie['genres'])}")
        print(f"Nota: {movie['vote_average']}/10")
        print(f"\nSinopse: {movie['overview'][:200]}...")
        
        if movie.get('cast'):
            print(f"\nElenco principal: {', '.join(movie['cast'][:3])}")
        
        if movie.get('director'):
            print(f"Diretor: {movie['director']}")
    else:
        print("❌ Filme não encontrado")
    
    pipeline.close()


def example_2_process_small_dataset():
    """Exemplo 2: Processar um dataset pequeno."""
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Processar dataset pequeno")
    print("=" * 60)
    
    # Carregar API key
    load_dotenv()
    api_key = os.getenv('TMDB_API_KEY')
    
    if not api_key:
        print("❌ API key não encontrada. Configure no arquivo .env")
        return
    
    # Criar dataset de exemplo
    import pandas as pd
    
    example_movies = pd.DataFrame([
        {'tmdb_id': 872585, 'title': 'Oppenheimer', 'year': 2023},
        {'tmdb_id': 346698, 'title': 'Barbie', 'year': 2023},
        {'tmdb_id': 438631, 'title': 'Dune', 'year': 2021},
        {'tmdb_id': 447365, 'title': 'Guardians of the Galaxy Vol. 3', 'year': 2023},
        {'tmdb_id': 502356, 'title': 'The Super Mario Bros. Movie', 'year': 2023}
    ])
    
    # Criar diretório de exemplos
    examples_dir = Path('examples')
    examples_dir.mkdir(exist_ok=True)
    
    input_file = examples_dir / 'example_input.csv'
    example_movies.to_csv(input_file, index=False)
    
    print(f"\n📄 Dataset de exemplo criado: {input_file}")
    print(f"   Total de filmes: {len(example_movies)}")
    
    # Processar dataset
    print("\n🚀 Iniciando processamento...\n")
    
    # Configurar logging
    log_file = Path('logs') / 'example.log'
    utils.setup_logging(log_file=str(log_file), log_level='INFO')
    
    pipeline = TMDbDataPipeline(api_key=api_key)
    
    try:
        results = pipeline.process_dataset(
            input_file=str(input_file),
            output_file='examples/example_output.csv'
        )
        
        print(f"\n✅ Processamento concluído!")
        print(f"   Filmes processados: {len(results)}")
        print(f"   Output: examples/example_output.csv")
        
    finally:
        pipeline.close()


def example_3_use_cache():
    """Exemplo 3: Demonstrar funcionamento do cache."""
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Cache em ação")
    print("=" * 60)
    
    # Carregar API key
    load_dotenv()
    api_key = os.getenv('TMDB_API_KEY')
    
    if not api_key:
        print("❌ API key não encontrada. Configure no arquivo .env")
        return
    
    # Primeira execução (sem cache)
    print("\n🔄 Primeira execução (sem cache)...")
    pipeline = TMDbDataPipeline(api_key=api_key)
    
    import time
    start = time.time()
    movie1 = pipeline.process_single_movie(title="The Matrix", year=1999)
    duration1 = time.time() - start
    
    print(f"✅ Filme buscado em {duration1:.2f}s (da API)")
    
    # Segunda execução (com cache)
    print("\n🔄 Segunda execução (do cache)...")
    start = time.time()
    movie2 = pipeline.process_single_movie(title="The Matrix", year=1999)
    duration2 = time.time() - start
    
    print(f"✅ Filme buscado em {duration2:.2f}s (do cache)")
    print(f"\n⚡ Speedup: {duration1/duration2:.1f}x mais rápido!")
    
    # Mostrar estatísticas de cache
    cache_stats = pipeline.cache.get_stats()
    print(f"\n📊 Estatísticas de cache:")
    print(f"   Tamanho: {cache_stats['size']} entradas")
    print(f"   Hits: {cache_stats['hits']}")
    print(f"   Misses: {cache_stats['misses']}")
    print(f"   Hit rate: {cache_stats['hit_rate']:.1f}%")
    
    pipeline.close()


def example_4_without_credits_and_keywords():
    """Exemplo 4: Processar sem créditos e keywords (mais rápido)."""
    print("\n" + "=" * 60)
    print("EXEMPLO 4: Processamento rápido (sem extras)")
    print("=" * 60)
    
    # Carregar API key
    load_dotenv()
    api_key = os.getenv('TMDB_API_KEY')
    
    if not api_key:
        print("❌ API key não encontrada. Configure no arquivo .env")
        return
    
    # Pipeline sem créditos e keywords
    print("\n⚡ Modo rápido: apenas campos essenciais")
    pipeline = TMDbDataPipeline(
        api_key=api_key,
        enable_credits=False,
        enable_keywords=False
    )
    
    movie = pipeline.process_single_movie(title="Avatar", year=2009)
    
    if movie:
        print("\n✅ Dados obtidos:")
        print(f"   Título: {movie['title']}")
        print(f"   Gêneros: {', '.join(movie['genres'])}")
        print(f"   Nota: {movie['vote_average']}/10")
        print(f"\n   ⚠️  Sem créditos: cast={movie.get('cast')}")
        print(f"   ⚠️  Sem keywords: keywords={movie.get('keywords')}")
    
    pipeline.close()


def main():
    """Executa todos os exemplos."""
    print("\n" + "🎬" * 30)
    print("TMDb Dataset Builder - Exemplos de Uso")
    print("🎬" * 30)
    
    try:
        # Executar exemplos
        example_1_single_movie()
        
        # Comentar para não fazer requisições desnecessárias
        # example_2_process_small_dataset()
        # example_3_use_cache()
        # example_4_without_credits_and_keywords()
        
        print("\n" + "=" * 60)
        print("✅ Exemplos executados com sucesso!")
        print("=" * 60)
        print("\n💡 Dicas:")
        print("   - Descomente outros exemplos em example_usage.py")
        print("   - Configure sua API key em .env")
        print("   - Veja README.md para mais informações")
        print()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("   Verifique se configurou a API key corretamente")


if __name__ == '__main__':
    main()