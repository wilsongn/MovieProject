"""
Fetcher de alto nível para buscar e enriquecer dados de filmes.

Este módulo implementa:
- Busca de filmes por ID ou título
- Extração de campos essenciais e opcionais
- Enriquecimento com créditos e keywords
- Integração com cache
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from . import config
from .tmdb_client import TMDbClient
from .cache_manager import CacheManager
from .validators import MovieValidator


logger = logging.getLogger(__name__)


class MovieFetcher:
    """Fetcher de alto nível para buscar dados enriquecidos de filmes."""
    
    def __init__(
        self,
        client: TMDbClient,
        cache_manager: Optional[CacheManager] = None,
        enable_credits: bool = None,
        enable_keywords: bool = None
    ):
        """
        Inicializa o MovieFetcher.
        
        Args:
            client: Cliente TMDb configurado
            cache_manager: Gerenciador de cache (opcional)
            enable_credits: Habilitar busca de créditos (padrão: config.ENABLE_CREDITS)
            enable_keywords: Habilitar busca de keywords (padrão: config.ENABLE_KEYWORDS)
        """
        self.client = client
        self.cache = cache_manager
        self.validator = MovieValidator()
        
        # Feature flags
        self.enable_credits = enable_credits if enable_credits is not None else config.ENABLE_CREDITS
        self.enable_keywords = enable_keywords if enable_keywords is not None else config.ENABLE_KEYWORDS
        
        logger.info(
            f"MovieFetcher inicializado "
            f"(credits={self.enable_credits}, keywords={self.enable_keywords})"
        )
    
    def fetch_by_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca filme por ID do TMDb.
        
        Este é o método preferido quando o ID está disponível.
        
        Args:
            tmdb_id: ID do filme no TMDb
            
        Returns:
            Dados enriquecidos do filme ou None se não encontrado/inválido
        """
        # Verificar cache
        if self.cache:
            cached = self.cache.get_by_id(tmdb_id)
            if cached:
                logger.debug(f"Filme encontrado no cache: ID {tmdb_id}")
                return cached
        
        # Buscar na API
        logger.debug(f"Buscando filme na API: ID {tmdb_id}")
        movie_data = self.client.get_movie_details(tmdb_id)
        
        if not movie_data:
            logger.warning(f"Filme não encontrado: ID {tmdb_id}")
            return None
        
        # Enriquecer dados
        enriched = self._enrich_movie_data(movie_data)
        
        # Validar
        is_valid, error_msg = self.validator.validate_movie(enriched)
        if not is_valid:
            logger.warning(f"Validação falhou para ID {tmdb_id}: {error_msg}")
            return None
        
        # Salvar no cache
        if self.cache:
            self.cache.set_movie(enriched)
        
        return enriched
    
    def fetch_by_title(
        self,
        title: str,
        year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca filme por título e opcionalmente ano.
        
        Args:
            title: Título do filme
            year: Ano de lançamento (opcional, melhora precisão)
            
        Returns:
            Dados enriquecidos do filme ou None se não encontrado/inválido
        """
        # Verificar cache
        if self.cache:
            cached = self.cache.get_by_title(title, year)
            if cached:
                logger.debug(f"Filme encontrado no cache: {title} ({year})")
                return cached
        
        # Buscar na API
        logger.debug(f"Buscando filme na API: {title} ({year})")
        search_result = self.client.search_movie(title, year)
        
        if not search_result:
            logger.warning(f"Filme não encontrado: {title} ({year})")
            return None
        
        # Obter ID do primeiro resultado
        tmdb_id = search_result.get('id')
        if not tmdb_id:
            logger.warning(f"Resultado sem ID: {title} ({year})")
            return None
        
        # Buscar detalhes completos
        return self.fetch_by_id(tmdb_id)
    
    def _enrich_movie_data(self, movie_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece dados básicos do filme com informações adicionais.
        
        Args:
            movie_data: Dados básicos do filme da API
            
        Returns:
            Dados enriquecidos e formatados
        """
        enriched = {}
        
        # Extrair campos essenciais
        enriched.update(self._extract_essential_fields(movie_data))
        
        # Extrair campos importantes
        enriched.update(self._extract_important_fields(movie_data))
        
        # Extrair campos opcionais
        enriched.update(self._extract_optional_fields(movie_data))
        
        # Extrair créditos se habilitado
        if self.enable_credits:
            tmdb_id = enriched.get('tmdb_id')
            if tmdb_id:
                credits_data = self._extract_credits(tmdb_id)
                enriched.update(credits_data)
        
        # Extrair keywords se habilitado
        if self.enable_keywords:
            tmdb_id = enriched.get('tmdb_id')
            if tmdb_id:
                keywords_data = self._extract_keywords(tmdb_id)
                enriched.update(keywords_data)
        
        return enriched
    
    def _extract_essential_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai campos essenciais do filme."""
        fields = {}
        
        # ID
        fields['tmdb_id'] = data.get('id')
        
        # Título
        fields['title'] = self.validator.sanitize_text(data.get('title', ''))
        
        # Sinopse
        fields['overview'] = self.validator.sanitize_text(data.get('overview', ''))
        
        # Data de lançamento
        release_date = data.get('release_date', '')
        fields['release_date'] = release_date
        
        # Extrair ano da data
        if release_date:
            try:
                year = datetime.strptime(release_date, '%Y-%m-%d').year
                fields['year'] = year
            except ValueError:
                fields['year'] = None
        else:
            fields['year'] = None
        
        return fields
    
    def _extract_important_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai campos importantes do filme."""
        fields = {}
        
        # Gêneros
        genres_data = data.get('genres', [])
        fields['genres'] = [g['name'] for g in genres_data]
        fields['genre_ids'] = [g['id'] for g in genres_data]
        
        # Avaliações
        fields['vote_average'] = data.get('vote_average')
        fields['vote_count'] = data.get('vote_count')
        fields['popularity'] = data.get('popularity')
        
        return fields
    
    def _extract_optional_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai campos opcionais do filme."""
        fields = {}
        
        fields['original_title'] = self.validator.sanitize_text(
            data.get('original_title', '')
        )
        fields['original_language'] = data.get('original_language')
        fields['runtime'] = data.get('runtime')
        fields['poster_path'] = data.get('poster_path')
        fields['backdrop_path'] = data.get('backdrop_path')
        fields['tagline'] = self.validator.sanitize_text(data.get('tagline', ''))
        fields['budget'] = data.get('budget')
        fields['revenue'] = data.get('revenue')
        
        return fields
    
    def _extract_credits(self, tmdb_id: int) -> Dict[str, Any]:
        """
        Extrai informações de créditos (elenco e diretor).
        
        Args:
            tmdb_id: ID do filme
            
        Returns:
            Dicionário com cast, cast_ids e director
        """
        credits = {
            'cast': [],
            'cast_ids': [],
            'director': None
        }
        
        credits_data = self.client.get_movie_credits(tmdb_id)
        
        if not credits_data:
            return credits
        
        # Extrair top N atores
        cast_list = credits_data.get('cast', [])
        top_cast = cast_list[:config.TOP_CAST_COUNT]
        credits['cast'] = [actor['name'] for actor in top_cast]
        credits['cast_ids'] = [actor['id'] for actor in top_cast]
        
        # Extrair diretor
        crew_list = credits_data.get('crew', [])
        directors = [
            person['name']
            for person in crew_list
            if person.get('job') == 'Director'
        ]
        
        if directors:
            credits['director'] = directors[0]  # Primeiro diretor
        
        return credits
    
    def _extract_keywords(self, tmdb_id: int) -> Dict[str, Any]:
        """
        Extrai palavras-chave temáticas do filme.
        
        Args:
            tmdb_id: ID do filme
            
        Returns:
            Dicionário com lista de keywords
        """
        keywords = {'keywords': []}
        
        keywords_data = self.client.get_movie_keywords(tmdb_id)
        
        if not keywords_data:
            return keywords
        
        keyword_list = keywords_data.get('keywords', [])
        keywords['keywords'] = [kw['name'] for kw in keyword_list]
        
        return keywords