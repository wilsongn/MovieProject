"""
Funções utilitárias para o TMDb Dataset Builder.

Este módulo contém helpers para:
- Formatação de tempo
- Manipulação de arquivos
- Estatísticas
- Conversão de dados
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from . import config


logger = logging.getLogger(__name__)


def format_duration(seconds: float) -> str:
    """
    Formata duração em formato legível.
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "2h 15m 33s")
    """
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if td.days > 0:
        parts.append(f"{td.days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def format_percentage(value: float, total: float) -> str:
    """
    Formata valor como porcentagem.
    
    Args:
        value: Valor parcial
        total: Valor total
        
    Returns:
        String formatada (ex: "87.4%")
    """
    if total == 0:
        return "0.0%"
    
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"


def ensure_directory(path: str) -> Path:
    """
    Garante que um diretório existe.
    
    Args:
        path: Caminho do diretório
        
    Returns:
        Path object do diretório
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def list_to_string(items: List[Any], separator: str = "|") -> str:
    """
    Converte lista para string separada.
    
    Args:
        items: Lista de items
        separator: Separador entre items
        
    Returns:
        String com items separados
    """
    if not items:
        return ""
    
    return separator.join(str(item) for item in items)


def string_to_list(text: str, separator: str = "|") -> List[str]:
    """
    Converte string separada para lista.
    
    Args:
        text: String com items separados
        separator: Separador entre items
        
    Returns:
        Lista de strings
    """
    if not text:
        return []
    
    return [item.strip() for item in text.split(separator)]


def prepare_row_for_csv(movie_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepara dicionário de filme para escrita em CSV.
    
    Converte listas para strings separadas por pipe (|).
    
    Args:
        movie_data: Dados do filme
        
    Returns:
        Dicionário preparado para CSV
    """
    row = {}
    
    for field in config.OUTPUT_SCHEMA:
        value = movie_data.get(field)
        
        # Converter listas para strings
        if isinstance(value, list):
            row[field] = list_to_string(value)
        # None vira string vazia
        elif value is None:
            row[field] = ""
        # Outros valores mantém como estão
        else:
            row[field] = value
    
    return row


def load_input_csv(file_path: str) -> pd.DataFrame:
    """
    Carrega CSV de input e valida formato.
    
    Args:
        file_path: Caminho do arquivo CSV
        
    Returns:
        DataFrame com os dados
        
    Raises:
        FileNotFoundError: Se arquivo não existe
        ValueError: Se formato do CSV é inválido
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Erro ao ler CSV: {e}")
    
    # Validar colunas mínimas
    if 'title' not in df.columns:
        raise ValueError("CSV deve conter coluna 'title'")
    
    # Aceitar com ou sem tmdb_id
    has_id = 'tmdb_id' in df.columns
    has_year = 'year' in df.columns
    
    if not has_id and not has_year:
        logger.warning("CSV sem 'year' - busca por título será menos precisa")
    
    logger.info(
        f"CSV carregado: {len(df)} filmes "
        f"(has_id={has_id}, has_year={has_year})"
    )
    
    return df


def save_dataframe_to_csv(df: pd.DataFrame, file_path: str):
    """
    Salva DataFrame em CSV.
    
    Args:
        df: DataFrame a ser salvo
        file_path: Caminho do arquivo de saída
    """
    path = Path(file_path)
    
    # Garantir que diretório existe
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Salvar com encoding UTF-8
    df.to_csv(path, index=False, encoding='utf-8')
    
    logger.info(f"CSV salvo: {file_path} ({len(df)} linhas)")


def print_statistics(stats: Dict[str, Any]):
    """
    Imprime estatísticas formatadas no console.
    
    Args:
        stats: Dicionário com estatísticas
    """
    print("\n" + "=" * 50)
    print("FETCHING STATISTICS")
    print("=" * 50)
    
    total = stats.get('total', 0)
    success = stats.get('success', 0)
    failed = stats.get('failed', 0)
    invalid = stats.get('invalid', 0)
    from_cache = stats.get('from_cache', 0)
    duration = stats.get('duration', 0)
    
    print(f"Total movies:    {total}")
    print(f"Success:         {success} ({format_percentage(success, total)})")
    print(f"Failed:          {failed} ({format_percentage(failed, total)})")
    print(f"Invalid:         {invalid} ({format_percentage(invalid, total)})")
    print(f"From cache:      {from_cache} ({format_percentage(from_cache, total)})")
    print(f"Execution time:  {format_duration(duration)}")
    
    print("=" * 50)
    
    # Cache statistics se disponível
    if 'cache_stats' in stats:
        cache_stats = stats['cache_stats']
        print("\nCACHE STATISTICS")
        print("-" * 50)
        print(f"Cache size:      {cache_stats.get('size', 0)} entries")
        print(f"Cache hits:      {cache_stats.get('hits', 0)}")
        print(f"Cache misses:    {cache_stats.get('misses', 0)}")
        print(f"Hit rate:        {cache_stats.get('hit_rate', 0):.1f}%")
        print("-" * 50)
    
    print()


def setup_logging(
    log_file: str = None,
    log_level: str = None,
    console: bool = True
):
    """
    Configura sistema de logging.
    
    Args:
        log_file: Caminho do arquivo de log (opcional)
        log_level: Nível de log (padrão: config.LOG_LEVEL)
        console: Se True, também loga no console
    """
    level = log_level or config.LOG_LEVEL
    
    # Configuração base
    handlers = []
    
    # Handler para arquivo
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                config.LOG_FORMAT,
                datefmt=config.LOG_DATE_FORMAT
            )
        )
        handlers.append(file_handler)
    
    # Handler para console
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(
            logging.Formatter(
                config.LOG_FORMAT,
                datefmt=config.LOG_DATE_FORMAT
            )
        )
        handlers.append(console_handler)
    
    # Configurar root logger
    logging.basicConfig(
        level=level,
        handlers=handlers
    )
    
    logger.info("Logging configurado")


def get_timestamp() -> str:
    """
    Retorna timestamp atual formatado.
    
    Returns:
        String no formato ISO (ex: "2026-02-08T14:30:00")
    """
    return datetime.now().isoformat()


def generate_checkpoint_filename(output_file: str) -> str:
    """
    Gera nome de arquivo de checkpoint.
    
    Args:
        output_file: Nome do arquivo de saída
        
    Returns:
        Nome do arquivo de checkpoint
    """
    path = Path(output_file)
    stem = path.stem
    suffix = path.suffix
    
    return str(path.parent / f"{stem}{config.CHECKPOINT_SUFFIX}")