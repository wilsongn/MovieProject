"""
TMDb Movie Dataset Builder

Um sistema robusto para construir datasets enriquecidos de filmes
usando a API do The Movie Database (TMDb).

Principais componentes:
- TMDbClient: Cliente HTTP de baixo nível
- MovieFetcher: Fetcher de alto nível para enriquecimento
- CacheManager: Sistema de cache persistente
- MovieValidator: Validação de qualidade de dados
- TMDbDataPipeline: Pipeline completo de processamento

Exemplo de uso:
    from data_fetcher import TMDbDataPipeline
    
    pipeline = TMDbDataPipeline(api_key="sua_chave")
    results = pipeline.process_dataset('movies.csv', 'movies_enriched.csv')
"""

__version__ = "1.0.0"
__author__ = "TMDb Dataset Builder Team"

from .tmdb_client import TMDbClient
from .movie_fetcher import MovieFetcher
from .cache_manager import CacheManager
from .validators import MovieValidator
from .main import TMDbDataPipeline

__all__ = [
    'TMDbClient',
    'MovieFetcher',
    'CacheManager',
    'MovieValidator',
    'TMDbDataPipeline'
]