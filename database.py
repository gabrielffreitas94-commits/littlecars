import sqlite3
from typing import Generator
from contextlib import contextmanager

DB_FILE = "cars.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabela de Marcas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            pais_origem TEXT,
            ano_fundacao INTEGER,
            descricao TEXT,
            site_oficial TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabela de Modelos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS modelos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca_id INTEGER NOT NULL REFERENCES marcas(id) ON DELETE CASCADE,
            nome TEXT NOT NULL,
            tipo_carroceria TEXT,
            ano_lancamento INTEGER,
            descricao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabela de Carrinhos (Itens Físicos / Exemplares na Coleção)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS carrinhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo_id INTEGER NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
            ano_fabricacao INTEGER,
            escala TEXT DEFAULT '1:64',
            cor TEXT NOT NULL,
            serie_colecao TEXT,
            condicao TEXT NOT NULL DEFAULT 'Blister/Cartela Fechada',
            codigo_barra_sku TEXT,
            localizacao TEXT,
            quantidade INTEGER NOT NULL DEFAULT 1,
            preco_compra REAL DEFAULT 0.0,
            valor_estimado REAL DEFAULT 0.0,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Verificar se precisa popular dados iniciais de demonstração
        cursor.execute("SELECT COUNT(*) as count FROM marcas;")
        if cursor.fetchone()["count"] == 0:
            seed_data(cursor)

def seed_data(cursor: sqlite3.Cursor):
    # Marcas
    marcas = [
        ("Hot Wheels", "EUA", 1968, "Famosa linha de carrinhos die-cast da Mattel.", "https://hotwheels.mattel.com"),
        ("Matchbox", "Reino Unido", 1953, "Linha histórica de veículos em miniatura detalhados e realistas.", "https://matchbox.mattel.com"),
        ("Tomica", "Japão", 1970, "Principal marca japonesa de miniaturas die-cast pela Takara Tomy.", "https://www.takaratomy.co.jp/products/tomica/"),
        ("Mini GT", "Hong Kong", 2017, "Miniaturas colecionáveis de alta precisão e detalhamento em escala 1:64.", "https://minigt.com"),
        ("Majorette", "França", 1961, "Tradicional fabricante francesa conhecida por suspensões ativas e portas móveis.", "https://www.majorette.com"),
    ]
    cursor.executemany("""
        INSERT INTO marcas (nome, pais_origem, ano_fundacao, descricao, site_oficial)
        VALUES (?, ?, ?, ?, ?);
    """, marcas)

    # Obter os IDs das marcas
    cursor.execute("SELECT id, nome FROM marcas;")
    marca_map = {row["nome"]: row["id"] for row in cursor.fetchall()}

    # Modelos
    modelos = [
        # Hot Wheels
        (marca_map["Hot Wheels"], "'67 Camaro", "Muscle Car", 1967, "Um dos lendários 'Sweet 16' originais de 1968 da Hot Wheels."),
        (marca_map["Hot Wheels"], "Nissan Skyline GT-R (BNR34)", "Esportivo JDM", 1999, "Ícone japonês cultuado em todo o mundo."),
        (marca_map["Hot Wheels"], "Porsche 911 GT3 RS", "Supercarro", 2018, "Monstro das pistas homologado para as ruas."),
        (marca_map["Hot Wheels"], "Bone Shaker", "Hot Rod Custom", 2006, "Design original icônico de Larry Wood com caveira na grade frontal."),
        (marca_map["Hot Wheels"], "1970 Dodge Charger R/T", "Muscle Car", 1970, "Lenda clássica americana de alta potência."),
        
        # Matchbox
        (marca_map["Matchbox"], "Land Rover Defender 110", "SUV / Off-road", 2020, "Veículo britânico robusto pronto para expedições."),
        (marca_map["Matchbox"], "1968 Toyota Hilux", "Picape Clássica", 1968, "Picape histórica indestrutível."),
        (marca_map["Matchbox"], "2020 Chevrolet Corvette C8", "Supercarro", 2020, "Primeiro Corvette com motor central traseiro."),

        # Tomica
        (marca_map["Tomica"], "Toyota GR Yaris", "Hatchback Esportivo", 2020, "Bólido de rali WRC para as ruas da Toyota Gazoo Racing."),
        (marca_map["Tomica"], "Nissan Fairlady Z Custom", "Esportivo JDM", 2023, "Nova geração da icônica linhagem Z com motor twin-turbo."),

        # Mini GT
        (marca_map["Mini GT"], "Lamborghini Huracán LB-Works", "Supercarro Custom", 2021, "Edição Liberty Walk com alargadores de para-lamas e asa traseira."),
        (marca_map["Mini GT"], "McLaren Senna", "Hipercarro", 2019, "Homenagem ao lendário piloto brasileiro Ayrton Senna."),

        # Majorette
        (marca_map["Majorette"], "Volkswagen Fusca 1303", "Clássico", 1973, "O clássico 'Beetle' com portas que abrem."),
    ]
    cursor.executemany("""
        INSERT INTO modelos (marca_id, nome, tipo_carroceria, ano_lancamento, descricao)
        VALUES (?, ?, ?, ?, ?);
    """, modelos)

    cursor.execute("SELECT id, nome FROM modelos;")
    modelo_map = {row["nome"]: row["id"] for row in cursor.fetchall()}

    # Carrinhos na Coleção / Estoque
    carrinhos = [
        (modelo_map["'67 Camaro"], 2022, "1:64", "Azul Metálico com Listras Brancas", "Hot Wheels - HW Flames", "Blister/Cartela Fechada", "HW-2022-045", "Estante A - Prateleira 1", 3, 14.90, 35.00, "Excelente estado, cartela sem amassados."),
        (modelo_map["Nissan Skyline GT-R (BNR34)"], 2023, "1:64", "Bayside Blue", "Hot Wheels - Fast & Furious Premium", "Blister/Cartela Fechada", "HW-FF-089", "Estante A - Prateleira 2", 2, 49.90, 120.00, "Pneus de borracha Real Riders."),
        (modelo_map["Porsche 911 GT3 RS"], 2024, "1:64", "Lizard Green", "Hot Wheels - Factory Fresh", "Loose - Impecável", "HW-2024-112", "Gaveta de Exposição 1", 1, 15.00, 25.00, "Fora da cartela, protegido em expositor acrílico individual."),
        (modelo_map["Bone Shaker"], 2021, "1:64", "Preto Fosco com Chamas Vermelhas", "Hot Wheels - HW Art Cars", "Loose - Impecável", "HW-2021-002", "Gaveta de Exposição 1", 4, 12.50, 20.00, "Versão clássica com motor cromado."),
        (modelo_map["1970 Dodge Charger R/T"], 2020, "1:64", "Laranja Hemi", "Hot Wheels - Muscle Mania", "Blister/Cartela Fechada", "HW-2020-033", "Caixa Box Organizadora #01", 1, 13.90, 30.00, "Última unidade em estoque."),
        (modelo_map["Land Rover Defender 110"], 2023, "1:64", "Verde Pangea com Teto Branco", "Matchbox - Moving Parts", "Blister/Cartela Fechada", "MB-2023-018", "Estante B - Prateleira 1", 2, 29.90, 50.00, "Portas traseiras abrem funcionalmente."),
        (modelo_map["1968 Toyota Hilux"], 2022, "1:64", "Amarelo Mostarda", "Matchbox - Retro Series", "Blister/Cartela Fechada", "MB-2022-077", "Estante B - Prateleira 2", 1, 14.90, 28.00, "Item difícil de encontrar."),
        (modelo_map["2020 Chevrolet Corvette C8"], 2023, "1:64", "Vermelho Torch Red", "Matchbox - Superfast", "Blister/Cartela Fechada", "MB-2023-104", "Estante B - Prateleira 3", 0, 16.90, 35.00, "Esgotado temporariamente - repor na próxima convenção."),
        (modelo_map["Toyota GR Yaris"], 2022, "1:60", "Branco Pérola", "Tomica - No. 50 Regular", "Caixa Original Fechada", "TOM-50-2022", "Caixa Box Japão #01", 2, 45.00, 85.00, "Edição japonesa importada com suspensão funcional."),
        (modelo_map["Nissan Fairlady Z Custom"], 2023, "1:60", "Amarelo Ikazuchi", "Tomica - Premium No. 09", "Caixa Original Fechada", "TOM-PR-009", "Caixa Box Japão #01", 3, 65.00, 110.00, "Linha Tomica Premium com rodas esportivas."),
        (modelo_map["Lamborghini Huracán LB-Works"], 2023, "1:64", "Cinza Nardo com Decalques", "Mini GT - TSM Exclusive", "Caixa Colecionador Lacrada", "MGT-00452", "Vitrine Principal de Destaque", 1, 129.90, 220.00, "Miniatura ultra-detalhada com retrovisores flexíveis e base gravada."),
        (modelo_map["McLaren Senna"], 2023, "1:64", "Laranja Mira McLaren", "Mini GT - Series No. 188", "Caixa Colecionador Lacrada", "MGT-00188", "Vitrine Principal de Destaque", 2, 135.00, 240.00, "Pintura oficial licenciada e interior detalhado."),
        (modelo_map["Volkswagen Fusca 1303"], 2021, "1:64", "Azul Claro Vintage", "Majorette - Vintage Deluxe", "Blister/Cartela Fechada", "MAJ-VNT-73", "Estante C - Prateleira 1", 3, 24.90, 45.00, "Acompanha caixinha de colecionador em metal."),
    ]
    cursor.executemany("""
        INSERT INTO carrinhos (
            modelo_id, ano_fabricacao, escala, cor, serie_colecao, condicao,
            codigo_barra_sku, localizacao, quantidade, preco_compra, valor_estimado, observacoes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, carrinhos)
