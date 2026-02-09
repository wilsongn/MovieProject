"""
Cliente HTTP de baixo nível para comunicação com a API do TMDb.

Este módulo implementa:
- Requisições HTTP com rate limiting
- Retry logic com backoff exponencial
- Tratamento de erros de API
- Logging de requisições
"""

import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config


logger = logging.getLogger(__name__)


class TMDbClient:
    """Cliente HTTP para comunicação com a API do TMDb v3."""
    
    def __init__(self, api_key: str):
        """
        Inicializa o cliente TMDb.
        
        Args:
            api_key: Chave de API do TMDb
            
        Raises:
            ValueError: Se api_key for vazia ou None
        """
        if not api_key:
            raise ValueError("API key é obrigatória")
        
        self.api_key = api_key
        self.base_url = config.TMDB_BASE_URL
        self.session = self._create_session()
        self.last_request_time = 0
        
        logger.info("TMDb Client inicializado")
    
    def _create_session(self) -> requests.Session:
        """
        Cria sessão HTTP com retry automático.
        
        Returns:
            Session configurada com retry logic
        """
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=config.RETRY_BACKOFF_FACTOR,
            status_forcelist=config.RETRYABLE_STATUS_CODES,
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _rate_limit(self):
        """
        Implementa rate limiting para respeitar limites da API.
        
        Garante que não fazemos mais de REQUESTS_PER_SECOND requisições.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < config.RATE_LIMIT_DELAY:
            sleep_time = config.RATE_LIMIT_DELAY - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Faz requisição HTTP à API com rate limiting e tratamento de erros.
        
        Args:
            endpoint: Endpoint da API (ex: "/search/movie")
            params: Parâmetros da query string
            
        Returns:
            Resposta JSON da API ou None se erro
            
        Raises:
            requests.exceptions.HTTPError: Para erros fatais (401, 403)
        """
        # Rate limiting
        self._rate_limit()
        
        # Preparar parâmetros
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        # Construir URL
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"GET {endpoint} | params: {params}")
            
            response = self.session.get(
                url,
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )
            
            # Verificar erros fatais
            if response.status_code in config.FATAL_STATUS_CODES:
                logger.error(f"Erro fatal: HTTP {response.status_code} - {response.text}")
                response.raise_for_status()
            
            # 404 = não encontrado (não é erro)
            if response.status_code == 404:
                logger.debug(f"Recurso não encontrado: {endpoint}")
                return None
            
            # Rate limit exceeded
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit atingido. Aguardando {retry_after}s")
                time.sleep(retry_after)
                # Tentar novamente
                return self._make_request(endpoint, params)
            
            # Outros erros
            if response.status_code >= 400:
                logger.error(f"HTTP {response.status_code}: {endpoint}")
                return None
            
            # Sucesso
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao acessar {endpoint}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede: {e}")
            return None
    
    def search_movie(
        self,
        title: str,
        year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca filme por título e opcionalmente por ano.
        
        Args:
            title: Título do filme
            year: Ano de lançamento (opcional)
            
        Returns:
            Primeiro resultado da busca ou None se não encontrado
        """
        params = {
            'query': title,
            'language': 'en-US',
            'page': 1
        }
        
        if year:
            params['year'] = year
        
        data = self._make_request(config.ENDPOINT_SEARCH, params)
        
        if not data or 'results' not in data:
            logger.warning(f"Filme não encontrado: {title} ({year})")
            return None
        
        results = data['results']
        
        if len(results) == 0:
            logger.warning(f"Nenhum resultado para: {title} ({year})")
            return None
        
        # Retornar primeiro resultado (mais relevante)
        logger.debug(f"Encontrado: {results[0].get('title')} (ID: {results[0].get('id')})")
        return results[0]
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca detalhes completos de um filme por ID.
        
        Args:
            movie_id: ID do filme no TMDb
            
        Returns:
            Dados completos do filme ou None se não encontrado
        """
        endpoint = config.ENDPOINT_MOVIE.format(movie_id=movie_id)
        params = {'language': 'en-US'}
        
        data = self._make_request(endpoint, params)
        
        if data:
            logger.debug(f"Detalhes obtidos: {data.get('title')} (ID: {movie_id})")
        else:
            logger.warning(f"Detalhes não encontrados para ID: {movie_id}")
        
        return data
    
    def get_movie_credits(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca créditos (elenco e equipe) de um filme.
        
        Args:
            movie_id: ID do filme no TMDb
            
        Returns:
            Dados de créditos ou None se não encontrado
        """
        endpoint = config.ENDPOINT_CREDITS.format(movie_id=movie_id)
        
        data = self._make_request(endpoint)
        
        if data:
            cast_count = len(data.get('cast', []))
            crew_count = len(data.get('crew', []))
            logger.debug(f"Créditos obtidos: {cast_count} cast, {crew_count} crew")
        else:
            logger.warning(f"Créditos não encontrados para ID: {movie_id}")
        
        return data
    
    def get_movie_keywords(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca palavras-chave temáticas de um filme.
        
        Args:
            movie_id: ID do filme no TMDb
            
        Returns:
            Lista de keywords ou None se não encontrado
        """
        endpoint = config.ENDPOINT_KEYWORDS.format(movie_id=movie_id)
        
        data = self._make_request(endpoint)
        
        if data:
            keyword_count = len(data.get('keywords', []))
            logger.debug(f"Keywords obtidas: {keyword_count}")
        else:
            logger.warning(f"Keywords não encontradas para ID: {movie_id}")
        
        return data
    
    def close(self):
        """Fecha a sessão HTTP."""
        self.session.close()
        logger.info("TMDb Client fechado")