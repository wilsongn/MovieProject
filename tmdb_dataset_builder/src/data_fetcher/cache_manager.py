"""
Gerenciador de cache persistente para o TMDb Dataset Builder.

Este módulo implementa:
- Cache em disco (JSON)
- Cache por ID e por título+ano
- Carregamento e salvamento automático
- Thread-safe operations
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock

from . import config


logger = logging.getLogger(__name__)


class CacheManager:
    """Gerenciador de cache persistente para dados de filmes."""
    
    def __init__(self, cache_dir: str = None):
        """
        Inicializa o gerenciador de cache.
        
        Args:
            cache_dir: Diretório para armazenar cache (padrão: config.CACHE_DIR)
        """
        self.cache_dir = Path(cache_dir or config.CACHE_DIR)
        self.cache_file = self.cache_dir / config.CACHE_FILE
        self.cache: Dict[str, Any] = {}
        self.lock = Lock()  # Thread safety
        self.hits = 0
        self.misses = 0
        
        # Criar diretório se não existir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Carregar cache existente
        self._load_cache()
        
        logger.info(f"Cache Manager inicializado: {len(self.cache)} entradas carregadas")
    
    def _load_cache(self):
        """Carrega cache do disco."""
        if not self.cache_file.exists():
            logger.info("Arquivo de cache não encontrado, iniciando cache vazio")
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
            logger.info(f"Cache carregado: {len(self.cache)} entradas")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar cache JSON: {e}")
            self.cache = {}
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Salva cache no disco."""
        try:
            with self.lock:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache salvo: {len(self.cache)} entradas")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    @staticmethod
    def _make_id_key(tmdb_id: int) -> str:
        """
        Cria chave de cache baseada em ID.
        
        Args:
            tmdb_id: ID do TMDb
            
        Returns:
            Chave no formato "id_{tmdb_id}"
        """
        return f"id_{tmdb_id}"
    
    @staticmethod
    def _make_title_key(title: str, year: Optional[int] = None) -> str:
        """
        Cria chave de cache baseada em título e ano.
        
        Args:
            title: Título do filme
            year: Ano de lançamento (opcional)
            
        Returns:
            Chave no formato "{title}_{year}" ou "{title}_unknown"
        """
        # Normalizar título (lowercase, sem espaços extras)
        title_normalized = title.lower().strip()
        year_str = str(year) if year else "unknown"
        return f"{title_normalized}_{year_str}"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Obtém item do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Dados do filme ou None se não encontrado
        """
        with self.lock:
            if key in self.cache:
                self.hits += 1
                logger.debug(f"Cache HIT: {key}")
                return self.cache[key]
            else:
                self.misses += 1
                logger.debug(f"Cache MISS: {key}")
                return None
    
    def get_by_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém filme do cache por ID.
        
        Args:
            tmdb_id: ID do TMDb
            
        Returns:
            Dados do filme ou None se não encontrado
        """
        key = self._make_id_key(tmdb_id)
        return self.get(key)
    
    def get_by_title(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Obtém filme do cache por título e ano.
        
        Args:
            title: Título do filme
            year: Ano de lançamento (opcional)
            
        Returns:
            Dados do filme ou None se não encontrado
        """
        key = self._make_title_key(title, year)
        return self.get(key)
    
    def set(self, key: str, value: Dict[str, Any]):
        """
        Adiciona item ao cache.
        
        Args:
            key: Chave do cache
            value: Dados do filme
        """
        with self.lock:
            # Adicionar timestamp
            value['fetched_at'] = datetime.now().isoformat()
            self.cache[key] = value
            logger.debug(f"Cache SET: {key}")
    
    def set_movie(self, movie_data: Dict[str, Any]):
        """
        Adiciona filme ao cache usando múltiplas chaves.
        
        Cria entradas tanto por ID quanto por título+ano para facilitar buscas.
        
        Args:
            movie_data: Dados completos do filme
        """
        if 'tmdb_id' in movie_data:
            # Armazenar por ID
            id_key = self._make_id_key(movie_data['tmdb_id'])
            self.set(id_key, movie_data)
        
        # Armazenar por título+ano
        if 'title' in movie_data:
            title = movie_data['title']
            year = movie_data.get('year')
            title_key = self._make_title_key(title, year)
            self.set(title_key, movie_data)
    
    def has(self, key: str) -> bool:
        """
        Verifica se chave existe no cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se existe, False caso contrário
        """
        with self.lock:
            return key in self.cache
    
    def has_id(self, tmdb_id: int) -> bool:
        """
        Verifica se filme existe no cache por ID.
        
        Args:
            tmdb_id: ID do TMDb
            
        Returns:
            True se existe, False caso contrário
        """
        key = self._make_id_key(tmdb_id)
        return self.has(key)
    
    def has_title(self, title: str, year: Optional[int] = None) -> bool:
        """
        Verifica se filme existe no cache por título.
        
        Args:
            title: Título do filme
            year: Ano de lançamento (opcional)
            
        Returns:
            True se existe, False caso contrário
        """
        key = self._make_title_key(title, year)
        return self.has(key)
    
    def clear(self):
        """Limpa todo o cache."""
        with self.lock:
            self.cache = {}
            self.hits = 0
            self.misses = 0
            logger.info("Cache limpo")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }
    
    def __len__(self) -> int:
        """Retorna número de entradas no cache."""
        return len(self.cache)
    
    def __contains__(self, key: str) -> bool:
        """Permite usar 'in' operator."""
        return self.has(key)