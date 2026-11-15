from django.db import migrations

def seed_data(apps, schema_editor):
    Marca = apps.get_model('colecao', 'Marca')
    Modelo = apps.get_model('colecao', 'Modelo')
    Carrinho = apps.get_model('colecao', 'Carrinho')

    if Marca.objects.exists():
        return

    # Marcas
    marcas_dados = [
        ("Hot Wheels", "EUA", 1968, "Famosa linha de carrinhos die-cast da Mattel.", "https://hotwheels.mattel.com"),
        ("Matchbox", "Reino Unido", 1953, "Linha histórica de veículos em miniatura detalhados e realistas.", "https://matchbox.mattel.com"),
        ("Tomica", "Japão", 1970, "Principal marca japonesa de miniaturas die-cast pela Takara Tomy.", "https://www.takaratomy.co.jp/products/tomica/"),
        ("Mini GT", "Hong Kong", 2017, "Miniaturas colecionáveis de alta precisão e detalhamento em escala 1:64.", "https://minigt.com"),
        ("Majorette", "França", 1961, "Tradicional fabricante francesa conhecida por suspensões ativas e portas móveis.", "https://www.majorette.com"),
    ]
    marcas = {}
    for nome, pais, ano, desc, site in marcas_dados:
        marcas[nome] = Marca.objects.create(
            nome=nome,
            pais_origem=pais,
            ano_fundacao=ano,
            descricao=desc,
            site_oficial=site
        )

    # Modelos
    modelos_dados = [
        # Hot Wheels
        ("Hot Wheels", "'67 Camaro", "Muscle Car", 1967, "Um dos lendários 'Sweet 16' originais de 1968 da Hot Wheels."),
        ("Hot Wheels", "Nissan Skyline GT-R (BNR34)", "Esportivo JDM", 1999, "Ícone japonês cultuado em todo o mundo."),
        ("Hot Wheels", "Porsche 911 GT3 RS", "Supercarro", 2018, "Monstro das pistas homologado para as ruas."),
        ("Hot Wheels", "Bone Shaker", "Hot Rod Custom", 2006, "Design original icônico de Larry Wood com caveira na grade frontal."),
        ("Hot Wheels", "1970 Dodge Charger R/T", "Muscle Car", 1970, "Lenda clássica americana de alta potência."),
        
        # Matchbox
        ("Matchbox", "Land Rover Defender 110", "SUV / Off-road", 2020, "Veículo britânico robusto pronto para expedições."),
        ("Matchbox", "1968 Toyota Hilux", "Picape Clássica", 1968, "Picape histórica indestrutível."),
        ("Matchbox", "2020 Chevrolet Corvette C8", "Supercarro", 2020, "Primeiro Corvette com motor central traseiro."),

        # Tomica
        ("Tomica", "Toyota GR Yaris", "Hatchback Esportivo", 2020, "Bólido de rali WRC para as ruas da Toyota Gazoo Racing."),
        ("Tomica", "Nissan Fairlady Z Custom", "Esportivo JDM", 2023, "Nova geração da icônica linhagem Z com motor twin-turbo."),

        # Mini GT
        ("Mini GT", "Lamborghini Huracán LB-Works", "Supercarro Custom", 2021, "Edição Liberty Walk com alargadores de para-lamas e asa traseira."),
        ("Mini GT", "McLaren Senna", "Hipercarro", 2019, "Homenagem ao lendário piloto brasileiro Ayrton Senna."),

        # Majorette
        ("Majorette", "Volkswagen Fusca 1303", "Clássico", 1973, "O clássico 'Beetle' com portas que abrem."),
    ]
    modelos = {}
    for marca_nome, nome, carroceria, ano, desc in modelos_dados:
        modelos[nome] = Modelo.objects.create(
            marca=marcas[marca_nome],
            nome=nome,
            tipo_carroceria=carroceria,
            ano_lancamento=ano,
            descricao=desc
        )

    # Carrinhos na Coleção / Estoque
    carrinhos_dados = [
        ("'67 Camaro", 2022, "1:64", "Azul Metálico com Listras Brancas", "Hot Wheels - HW Flames", "Blister/Cartela Fechada", "HW-2022-045", "Estante A - Prateleira 1", 3, 14.90, 35.00, "Excelente estado, cartela sem amassados."),
        ("Nissan Skyline GT-R (BNR34)", 2023, "1:64", "Bayside Blue", "Hot Wheels - Fast & Furious Premium", "Blister/Cartela Fechada", "HW-FF-089", "Estante A - Prateleira 2", 2, 49.90, 120.00, "Pneus de borracha Real Riders."),
        ("Porsche 911 GT3 RS", 2024, "1:64", "Lizard Green", "Hot Wheels - Factory Fresh", "Loose - Impecável", "HW-2024-112", "Gaveta de Exposição 1", 1, 15.00, 25.00, "Fora da cartela, protegido em expositor acrílico individual."),
        ("Bone Shaker", 2021, "1:64", "Preto Fosco com Chamas Vermelhas", "Hot Wheels - HW Art Cars", "Loose - Impecável", "HW-2021-002", "Gaveta de Exposição 1", 4, 12.50, 20.00, "Versão clássica com motor cromado."),
        ("1970 Dodge Charger R/T", 2020, "1:64", "Laranja Hemi", "Hot Wheels - Muscle Mania", "Blister/Cartela Fechada", "HW-2020-033", "Caixa Box Organizadora #01", 1, 13.90, 30.00, "Última unidade em estoque."),
        ("Land Rover Defender 110", 2023, "1:64", "Verde Pangea com Teto Branco", "Matchbox - Moving Parts", "Blister/Cartela Fechada", "MB-2023-018", "Estante B - Prateleira 1", 2, 29.90, 50.00, "Portas traseiras abrem funcionalmente."),
        ("1968 Toyota Hilux", 2022, "1:64", "Amarelo Mostarda", "Matchbox - Retro Series", "Blister/Cartela Fechada", "MB-2022-077", "Estante B - Prateleira 2", 1, 14.90, 28.00, "Item difícil de encontrar."),
        ("2020 Chevrolet Corvette C8", 2023, "1:64", "Vermelho Torch Red", "Matchbox - Superfast", "Blister/Cartela Fechada", "MB-2023-104", "Estante B - Prateleira 3", 0, 16.90, 35.00, "Esgotado temporariamente - repor na próxima convenção."),
        ("Toyota GR Yaris", 2022, "1:60", "Branco Pérola", "Tomica - No. 50 Regular", "Caixa Original Fechada", "TOM-50-2022", "Caixa Box Japão #01", 2, 45.00, 85.00, "Edição japonesa importada com suspensão funcional."),
        ("Nissan Fairlady Z Custom", 2023, "1:60", "Amarelo Ikazuchi", "Tomica - Premium No. 09", "Caixa Original Fechada", "TOM-PR-009", "Caixa Box Japão #01", 3, 65.00, 110.00, "Linha Tomica Premium com rodas esportivas."),
        ("Lamborghini Huracán LB-Works", 2023, "1:64", "Cinza Nardo com Decalques", "Mini GT - TSM Exclusive", "Caixa Colecionador Lacrada", "MGT-00452", "Vitrine Principal de Destaque", 1, 129.90, 220.00, "Miniatura ultra-detalhada com retrovisores flexíveis e base gravada."),
        ("McLaren Senna", 2023, "1:64", "Laranja Mira McLaren", "Mini GT - Series No. 188", "Caixa Colecionador Lacrada", "MGT-00188", "Vitrine Principal de Destaque", 2, 135.00, 240.00, "Pintura oficial licenciada e interior detalhado."),
        ("Volkswagen Fusca 1303", 2021, "1:64", "Azul Claro Vintage", "Majorette - Vintage Deluxe", "Blister/Cartela Fechada", "MAJ-VNT-73", "Estante C - Prateleira 1", 3, 24.90, 45.00, "Acompanha caixinha de colecionador em metal."),
    ]
    for mod_nome, ano, escala, cor, serie, cond, sku, loc, qtd, compra, est, obs in carrinhos_dados:
        Carrinho.objects.create(
            modelo=modelos[mod_nome],
            ano_fabricacao=ano,
            escala=escala,
            cor=cor,
            serie_colecao=serie,
            condicao=cond,
            codigo_barra_sku=sku,
            localizacao=loc,
            quantidade=qtd,
            preco_compra=compra,
            valor_estimado=est,
            observacoes=obs
        )

def unseed_data(apps, schema_editor):
    Marca = apps.get_model('colecao', 'Marca')
    Marca.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('colecao', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
