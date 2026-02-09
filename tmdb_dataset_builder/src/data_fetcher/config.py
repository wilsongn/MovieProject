"""
Configurações e constantes do TMDb Dataset Builder.

Este módulo centraliza todas as configurações da aplicação.
"""

# ==============================================================================
# API CONFIGURATION
# ==============================================================================

TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Endpoints
ENDPOINT_SEARCH = "/search/movie"
ENDPOINT_MOVIE = "/movie/{movie_id}"
ENDPOINT_CREDITS = "/movie/{movie_id}/credits"
ENDPOINT_KEYWORDS = "/movie/{movie_id}/keywords"

# Rate Limiting (TMDb permite 50 req/s, usamos 45 com margem de segurança)
REQUESTS_PER_SECOND = 45
RATE_LIMIT_DELAY = 1.0 / REQUESTS_PER_SECOND  # ~0.022 segundos

# Retry Configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Backoff exponencial: 1s, 2s, 4s
INITIAL_RETRY_DELAY = 1.0  # Segundos

# Timeout Configuration
REQUEST_TIMEOUT = 10  # segundos


# ==============================================================================
# CACHE CONFIGURATION
# ==============================================================================

CACHE_DIR = "cache"
CACHE_FILE = "tmdb_cache.json"
ENABLE_CACHE = True


# ==============================================================================
# OUTPUT CONFIGURATION
# ==============================================================================

OUTPUT_DIR = "processed"
LOG_DIR = "logs"
LOG_FILE = "tmdb_fetcher.log"

# Checkpoint Configuration
CHECKPOINT_INTERVAL = 100  # Salvar a cada N filmes
CHECKPOINT_SUFFIX = "_checkpoint.csv"


# ==============================================================================
# DATA VALIDATION RULES
# ==============================================================================

# Overview/sinopse
MIN_OVERVIEW_LENGTH = 20  # caracteres mínimos

# Ano de lançamento
MIN_YEAR = 1888  # Primeiro filme da história
MAX_YEAR = 2030  # Filmes futuros anunciados

# Campos obrigatórios
REQUIRED_FIELDS = ["tmdb_id", "title", "overview", "release_date"]

# Número mínimo de gêneros
MIN_GENRES = 1


# ==============================================================================
# FEATURE FLAGS
# ==============================================================================

# Habilitar busca de créditos (cast/director)
ENABLE_CREDITS = True

# Habilitar busca de keywords
ENABLE_KEYWORDS = True

# Top N atores para incluir
TOP_CAST_COUNT = 10


# ==============================================================================
# DATASET SCHEMA
# ==============================================================================

# Campos essenciais (sempre presentes)
ESSENTIAL_FIELDS = [
    "tmdb_id",
    "title",
    "overview",
    "release_date",
    "year"
]

# Campos importantes (presentes quando disponíveis)
IMPORTANT_FIELDS = [
    "genres",
    "genre_ids",
    "vote_average",
    "vote_count",
    "popularity"
]

# Campos opcionais (extras)
OPTIONAL_FIELDS = [
    "original_title",
    "original_language",
    "runtime",
    "poster_path",
    "backdrop_path",
    "tagline",
    "budget",
    "revenue"
]

# Campos de créditos (se ENABLE_CREDITS = True)
CREDITS_FIELDS = [
    "cast",
    "cast_ids",
    "director"
]

# Campos de keywords (se ENABLE_KEYWORDS = True)
KEYWORDS_FIELDS = [
    "keywords"
]

# Schema completo do output CSV (ordem das colunas)
OUTPUT_SCHEMA = (
    ESSENTIAL_FIELDS +
    IMPORTANT_FIELDS +
    OPTIONAL_FIELDS +
    (CREDITS_FIELDS if ENABLE_CREDITS else []) +
    (KEYWORDS_FIELDS if ENABLE_KEYWORDS else [])
)


# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ==============================================================================
# HTTP ERROR CODES
# ==============================================================================

# Códigos que devem fazer retry
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]

# Códigos que indicam erro fatal (não fazer retry)
FATAL_STATUS_CODES = [401, 403]


# ==============================================================================
# PROGRESS BAR CONFIGURATION
# ==============================================================================

PROGRESS_BAR_FORMAT = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
PROGRESS_BAR_COLOUR = "green"