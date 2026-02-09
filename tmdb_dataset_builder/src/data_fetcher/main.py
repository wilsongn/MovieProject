"""
Pipeline principal para construção do dataset de filmes TMDb.

Este módulo orquestra todo o processo de:
- Carregamento de dados de entrada
- Busca e enriquecimento via API
- Validação de dados
- Checkpoints automáticos
- Geração de estatísticas
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from tqdm import tqdm

from . import config
from .tmdb_client import TMDbClient
from .movie_fetcher import MovieFetcher
from .cache_manager import CacheManager
from .validators import MovieValidator
from . import utils


logger = logging.getLogger(__name__)


class TMDbDataPipeline:
    """Pipeline principal para construção do dataset de filmes."""
    
    def __init__(
        self,
        api_key: str,
        cache_dir: str = None,
        enable_cache: bool = True,
        enable_credits: bool = None,
        enable_keywords: bool = None
    ):
        """
        Inicializa o pipeline de dados.
        
        Args:
            api_key: Chave de API do TMDb
            cache_dir: Diretório para cache (padrão: config.CACHE_DIR)
            enable_cache: Habilitar sistema de cache
            enable_credits: Habilitar busca de créditos
            enable_keywords: Habilitar busca de keywords
        """
        logger.info("Inicializando TMDb Data Pipeline...")
        
        # Componentes principais
        self.client = TMDbClient(api_key)
        
        # Cache
        self.cache = None
        if enable_cache:
            self.cache = CacheManager(cache_dir)
        
        # Fetcher
        self.fetcher = MovieFetcher(
            self.client,
            self.cache,
            enable_credits,
            enable_keywords
        )
        
        self.validator = MovieValidator()
        
        # Estatísticas
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'invalid': 0,
            'from_cache': 0,
            'duration': 0
        }
        
        logger.info("Pipeline inicializado com sucesso")
    
    def process_dataset(
        self,
        input_file: str,
        output_file: str = None,
        save_checkpoints: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Processa dataset completo de filmes.
        
        Args:
            input_file: Caminho do CSV de entrada
            output_file: Caminho do CSV de saída (padrão: auto-gerado)
            save_checkpoints: Salvar checkpoints automáticos
            
        Returns:
            Lista de dicionários com dados dos filmes processados
        """
        start_time = time.time()
        
        logger.info(f"Iniciando processamento de {input_file}")
        
        # Carregar input
        df_input = utils.load_input_csv(input_file)
        self.stats['total'] = len(df_input)
        
        # Determinar arquivo de saída
        if output_file is None:
            output_file = self._generate_output_filename(input_file)
        
        output_path = Path(output_file)
        checkpoint_file = utils.generate_checkpoint_filename(output_file)
        
        # Processar filmes
        results = []
        
        with tqdm(
            total=len(df_input),
            desc="Processando filmes",
            bar_format=config.PROGRESS_BAR_FORMAT,
            colour=config.PROGRESS_BAR_COLOUR
        ) as pbar:
            
            for idx, row in df_input.iterrows():
                # Extrair dados da linha
                title = row.get('title')
                year = row.get('year')
                tmdb_id = row.get('tmdb_id')
                
                # Buscar filme
                movie_data = self._fetch_movie(title, year, tmdb_id)
                
                if movie_data:
                    results.append(movie_data)
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1
                
                # Atualizar progress bar
                pbar.update(1)
                pbar.set_postfix({
                    'success': self.stats['success'],
                    'failed': self.stats['failed']
                })
                
                # Checkpoint
                if save_checkpoints and len(results) % config.CHECKPOINT_INTERVAL == 0:
                    self._save_checkpoint(results, checkpoint_file)
        
        # Salvar resultado final
        self._save_results(results, output_path)
        
        # Salvar cache
        if self.cache:
            self.cache.save_cache()
        
        # Calcular duração
        self.stats['duration'] = time.time() - start_time
        
        # Adicionar estatísticas de cache
        if self.cache:
            self.stats['cache_stats'] = self.cache.get_stats()
            self.stats['from_cache'] = self.cache.hits
        
        # Imprimir estatísticas
        utils.print_statistics(self.stats)
        
        logger.info(f"Processamento concluído: {output_file}")
        
        return results
    
    def _fetch_movie(
        self,
        title: str,
        year: Optional[int],
        tmdb_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Busca dados de um filme.
        
        Prioriza busca por ID se disponível.
        
        Args:
            title: Título do filme
            year: Ano de lançamento (opcional)
            tmdb_id: ID do TMDb (opcional)
            
        Returns:
            Dados do filme ou None se não encontrado/inválido
        """
        try:
            # Buscar por ID (preferido)
            if tmdb_id and self.validator.is_valid_tmdb_id(tmdb_id):
                movie_data = self.fetcher.fetch_by_id(int(tmdb_id))
            # Buscar por título
            else:
                movie_data = self.fetcher.fetch_by_title(title, year)
            
            if not movie_data:
                logger.warning(
                    f"Filme não encontrado: {title} "
                    f"({'ID: ' + str(tmdb_id) if tmdb_id else 'year: ' + str(year)})"
                )
                return None
            
            return movie_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar filme '{title}': {e}")
            return None
    
    def _save_checkpoint(self, results: List[Dict[str, Any]], checkpoint_file: str):
        """
        Salva checkpoint do progresso.
        
        Args:
            results: Lista de resultados até o momento
            checkpoint_file: Arquivo de checkpoint
        """
        try:
            df = self._results_to_dataframe(results)
            utils.save_dataframe_to_csv(df, checkpoint_file)
            logger.info(f"Checkpoint salvo: {len(results)} filmes")
        except Exception as e:
            logger.error(f"Erro ao salvar checkpoint: {e}")
    
    def _save_results(self, results: List[Dict[str, Any]], output_file: Path):
        """
        Salva resultados finais em CSV.
        
        Args:
            results: Lista de filmes processados
            output_file: Arquivo de saída
        """
        df = self._results_to_dataframe(results)
        utils.save_dataframe_to_csv(df, str(output_file))
        
        logger.info(f"Dataset final salvo: {output_file} ({len(results)} filmes)")
    
    def _results_to_dataframe(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Converte lista de resultados para DataFrame.
        
        Args:
            results: Lista de dicionários de filmes
            
        Returns:
            DataFrame com schema correto
        """
        # Preparar linhas para CSV
        rows = [utils.prepare_row_for_csv(movie) for movie in results]
        
        # Criar DataFrame com schema correto
        df = pd.DataFrame(rows, columns=config.OUTPUT_SCHEMA)
        
        return df
    
    def _generate_output_filename(self, input_file: str) -> str:
        """
        Gera nome de arquivo de saída baseado no input.
        
        Args:
            input_file: Nome do arquivo de entrada
            
        Returns:
            Nome do arquivo de saída
        """
        input_path = Path(input_file)
        stem = input_path.stem
        
        output_dir = utils.ensure_directory(config.OUTPUT_DIR)
        output_file = output_dir / f"{stem}_enriched.csv"
        
        return str(output_file)
    
    def process_single_movie(
        self,
        title: str = None,
        year: int = None,
        tmdb_id: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Processa um único filme (útil para testes).
        
        Args:
            title: Título do filme
            year: Ano de lançamento
            tmdb_id: ID do TMDb
            
        Returns:
            Dados do filme ou None
        """
        if not title and not tmdb_id:
            raise ValueError("Forneça 'title' ou 'tmdb_id'")
        
        return self._fetch_movie(title, year, tmdb_id)
    
    def close(self):
        """Fecha recursos do pipeline."""
        if self.client:
            self.client.close()
        
        if self.cache:
            self.cache.save_cache()
        
        logger.info("Pipeline fechado")


def main():
    """
    Função principal para execução via CLI.
    
    Exemplo de uso:
        python main.py
    """
    import argparse
    import os
    from dotenv import load_dotenv
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Parser de argumentos
    parser = argparse.ArgumentParser(
        description="TMDb Movie Dataset Builder"
    )
    
    parser.add_argument(
        '--input',
        '-i',
        required=True,
        help='Arquivo CSV de entrada'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        help='Arquivo CSV de saída (opcional)'
    )
    
    parser.add_argument(
        '--api-key',
        help='Chave de API do TMDb (ou use variável TMDB_API_KEY)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Desabilitar cache'
    )
    
    parser.add_argument(
        '--no-credits',
        action='store_true',
        help='Desabilitar busca de créditos'
    )
    
    parser.add_argument(
        '--no-keywords',
        action='store_true',
        help='Desabilitar busca de keywords'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Nível de log'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    log_file = Path(config.LOG_DIR) / config.LOG_FILE
    utils.setup_logging(
        log_file=str(log_file),
        log_level=args.log_level
    )
    
    # Obter API key
    api_key = args.api_key or os.getenv('TMDB_API_KEY')
    
    if not api_key:
        logger.error("API key não fornecida. Use --api-key ou variável TMDB_API_KEY")
        return
    
    # Inicializar pipeline
    pipeline = TMDbDataPipeline(
        api_key=api_key,
        enable_cache=not args.no_cache,
        enable_credits=not args.no_credits,
        enable_keywords=not args.no_keywords
    )
    
    try:
        # Processar dataset
        pipeline.process_dataset(
            input_file=args.input,
            output_file=args.output
        )
    finally:
        # Garantir fechamento
        pipeline.close()


if __name__ == '__main__':
    main()