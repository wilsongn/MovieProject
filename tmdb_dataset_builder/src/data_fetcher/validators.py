"""
Validadores de dados para o TMDb Dataset Builder.

Este módulo implementa regras de validação para garantir qualidade dos dados.
"""

import logging
from typing import Dict, Any, Tuple

from . import config


logger = logging.getLogger(__name__)


class MovieValidator:
    """Validador de dados de filmes."""
    
    @staticmethod
    def validate_movie(movie_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida se um filme possui dados de qualidade suficiente.
        
        Regras de validação:
        1. Campos obrigatórios presentes
        2. Sinopse tem pelo menos 20 caracteres
        3. Ano está entre 1888-2030
        4. Pelo menos 1 gênero presente
        5. Overview não é string vazia
        
        Args:
            movie_data: Dicionário com dados do filme
            
        Returns:
            Tupla (is_valid, error_message)
            - is_valid: True se válido, False caso contrário
            - error_message: Mensagem de erro (vazia se válido)
        """
        # Validação 1: Campos obrigatórios
        for field in config.REQUIRED_FIELDS:
            if field not in movie_data or movie_data[field] is None:
                msg = f"Campo obrigatório ausente: {field}"
                logger.debug(f"Validação falhou: {msg}")
                return False, msg
        
        # Validação 2: Overview tem tamanho mínimo
        overview = movie_data.get('overview', '')
        if len(overview) < config.MIN_OVERVIEW_LENGTH:
            msg = f"Overview muito curto: {len(overview)} caracteres (mínimo: {config.MIN_OVERVIEW_LENGTH})"
            logger.debug(f"Validação falhou: {msg}")
            return False, msg
        
        # Validação 3: Overview não é string vazia
        if not overview.strip():
            msg = "Overview é string vazia"
            logger.debug(f"Validação falhou: {msg}")
            return False, msg
        
        # Validação 4: Ano válido
        year = movie_data.get('year')
        if year is not None:
            try:
                year_int = int(year)
                if year_int < config.MIN_YEAR or year_int > config.MAX_YEAR:
                    msg = f"Ano fora do intervalo válido: {year_int} (permitido: {config.MIN_YEAR}-{config.MAX_YEAR})"
                    logger.debug(f"Validação falhou: {msg}")
                    return False, msg
            except (ValueError, TypeError):
                msg = f"Ano inválido: {year}"
                logger.debug(f"Validação falhou: {msg}")
                return False, msg
        
        # Validação 5: Pelo menos 1 gênero
        genres = movie_data.get('genres', [])
        if not genres or len(genres) < config.MIN_GENRES:
            msg = f"Gêneros insuficientes: {len(genres)} (mínimo: {config.MIN_GENRES})"
            logger.debug(f"Validação falhou: {msg}")
            return False, msg
        
        # Todas as validações passaram
        logger.debug(f"Validação OK: {movie_data.get('title')}")
        return True, ""
    
    @staticmethod
    def is_valid_tmdb_id(tmdb_id: Any) -> bool:
        """
        Verifica se um TMDb ID é válido.
        
        Args:
            tmdb_id: ID a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            id_int = int(tmdb_id)
            return id_int > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_year(year: Any) -> bool:
        """
        Verifica se um ano é válido.
        
        Args:
            year: Ano a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            year_int = int(year)
            return config.MIN_YEAR <= year_int <= config.MAX_YEAR
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Limpa e sanitiza texto removendo caracteres problemáticos.
        
        Args:
            text: Texto a ser sanitizado
            
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        # Remover quebras de linha problemáticas
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remover múltiplos espaços
        text = ' '.join(text.split())
        
        # Remover aspas duplas problemáticas para CSV
        text = text.replace('"', "'")
        
        return text.strip()