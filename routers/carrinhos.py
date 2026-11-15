import json
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db

router = APIRouter(prefix="/carrinhos", tags=["carrinhos"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
def listar_carrinhos(
    request: Request,
    busca: str = "",
    marca_id: str = "",
    condicao: str = "",
    localizacao: str = "",
    view: str = "cards"
):
    with get_db() as conn:
        cursor = conn.cursor()

        # Marcas para filtro
        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

        # Localizações existentes para o filtro
        cursor.execute("SELECT DISTINCT localizacao FROM carrinhos WHERE localizacao IS NOT NULL AND localizacao != '' ORDER BY localizacao ASC")
        localizacoes = [r["localizacao"] for r in cursor.fetchall()]

        # Query principal
        query = """
            SELECT c.*, 
                   m.nome as modelo_nome, m.tipo_carroceria, m.ano_lancamento as modelo_ano,
                   ma.id as marca_id, ma.nome as marca_nome, ma.pais_origem as marca_pais
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            WHERE 1=1
        """
        params = []

        if busca:
            query += " AND (m.nome LIKE ? OR c.cor LIKE ? OR c.serie_colecao LIKE ? OR c.codigo_barra_sku LIKE ? OR ma.nome LIKE ?)"
            params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%", f"%{busca}%", f"%{busca}%"])

        if marca_id and marca_id.isdigit():
            query += " AND ma.id = ?"
            params.append(int(marca_id))

        if condicao:
            query += " AND c.condicao = ?"
            params.append(condicao)

        if localizacao:
            query += " AND c.localizacao = ?"
            params.append(localizacao)

        query += " ORDER BY c.id DESC"

        cursor.execute(query, params)
        carrinhos = cursor.fetchall()

        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM carrinhos")
        total_estoque = cursor.fetchone()["total"]

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx and ("busca" in request.query_params or "marca_id" in request.query_params or "condicao" in request.query_params or "localizacao" in request.query_params or "view" in request.query_params):
        return templates.TemplateResponse("carrinhos/partials/list.html", {
            "request": request,
            "carrinhos": carrinhos,
            "view": view
        })

    return templates.TemplateResponse("carrinhos/index.html", {
        "request": request,
        "carrinhos": carrinhos,
        "marcas": marcas,
        "localizacoes": localizacoes,
        "busca": busca,
        "marca_id_selecionada": int(marca_id) if marca_id and marca_id.isdigit() else 0,
        "condicao_selecionada": condicao,
        "localizacao_selecionada": localizacao,
        "view": view,
        "active_page": "carrinhos",
        "total_itens_estoque": total_estoque
    })

@router.get("/novo", response_class=HTMLResponse)
def form_novo_carrinho(request: Request, marca_id: int = 0):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

        # Se houver uma marca selecionada, pega modelos dela
        if marca_id > 0:
            cursor.execute("SELECT id, nome, tipo_carroceria FROM modelos WHERE marca_id = ? ORDER BY nome ASC", (marca_id,))
        else:
            cursor.execute("SELECT m.id, m.nome, m.tipo_carroceria, ma.nome as marca_nome FROM modelos m JOIN marcas ma ON m.marca_id = ma.id ORDER BY ma.nome ASC, m.nome ASC")
        modelos = cursor.fetchall()

        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM carrinhos")
        total_estoque = cursor.fetchone()["total"]

    return templates.TemplateResponse("carrinhos/form.html", {
        "request": request,
        "carrinho": None,
        "marcas": marcas,
        "modelos": modelos,
        "marca_selecionada_id": marca_id,
        "titulo": "Adicionar Novo Carrinho à Coleção",
        "active_page": "carrinhos",
        "total_itens_estoque": total_estoque
    })

@router.get("/{id}", response_class=HTMLResponse)
def detalhe_carrinho(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, 
                   m.nome as modelo_nome, m.tipo_carroceria, m.ano_lancamento as modelo_ano, m.descricao as modelo_desc,
                   ma.id as marca_id, ma.nome as marca_nome, ma.pais_origem as marca_pais, ma.site_oficial as marca_site
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            WHERE c.id = ?
        """, (id,))
        carrinho = cursor.fetchone()
        if not carrinho:
            raise HTTPException(status_code=404, detail="Carrinho não encontrado")

        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM carrinhos")
        total_estoque = cursor.fetchone()["total"]

    return templates.TemplateResponse("carrinhos/detail.html", {
        "request": request,
        "carrinho": carrinho,
        "active_page": "carrinhos",
        "total_itens_estoque": total_estoque
    })

@router.get("/{id}/editar", response_class=HTMLResponse)
def form_editar_carrinho(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, m.marca_id
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            WHERE c.id = ?
        """, (id,))
        carrinho = cursor.fetchone()
        if not carrinho:
            raise HTTPException(status_code=404, detail="Carrinho não encontrado")

        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

        cursor.execute("SELECT id, nome, tipo_carroceria FROM modelos WHERE marca_id = ? ORDER BY nome ASC", (carrinho["marca_id"],))
        modelos = cursor.fetchall()

        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM carrinhos")
        total_estoque = cursor.fetchone()["total"]

    return templates.TemplateResponse("carrinhos/form.html", {
        "request": request,
        "carrinho": carrinho,
        "marcas": marcas,
        "modelos": modelos,
        "marca_selecionada_id": carrinho["marca_id"],
        "titulo": f"Editar Carrinho #{carrinho['id']}",
        "active_page": "carrinhos",
        "total_itens_estoque": total_estoque
    })

@router.post("", response_class=HTMLResponse)
def criar_carrinho(
    request: Request,
    modelo_id: int = Form(...),
    ano_fabricacao: str = Form(""),
    escala: str = Form("1:64"),
    cor: str = Form(...),
    serie_colecao: str = Form(""),
    condicao: str = Form("Blister/Cartela Fechada"),
    codigo_barra_sku: str = Form(""),
    localizacao: str = Form(""),
    quantidade: int = Form(1),
    preco_compra: str = Form("0.0"),
    valor_estimado: str = Form("0.0"),
    observacoes: str = Form("")
):
    ano = int(ano_fabricacao) if ano_fabricacao and ano_fabricacao.isdigit() else None
    
    # Tratamento para preço e valor
    try:
        preco = float(preco_compra.replace(",", ".")) if preco_compra else 0.0
    except ValueError:
        preco = 0.0

    try:
        valor = float(valor_estimado.replace(",", ".")) if valor_estimado else 0.0
    except ValueError:
        valor = 0.0

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO carrinhos (
                modelo_id, ano_fabricacao, escala, cor, serie_colecao, condicao,
                codigo_barra_sku, localizacao, quantidade, preco_compra, valor_estimado, observacoes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            modelo_id, ano, escala.strip(), cor.strip(), serie_colecao.strip(), condicao.strip(),
            codigo_barra_sku.strip(), localizacao.strip(), max(0, quantidade), preco, valor, observacoes.strip()
        ))
        novo_id = cursor.lastrowid

    return RedirectResponse(url=f"/carrinhos/{novo_id}?cadastrado=true", status_code=303)

@router.post("/{id}/editar", response_class=HTMLResponse)
def atualizar_carrinho(
    request: Request,
    id: int,
    modelo_id: int = Form(...),
    ano_fabricacao: str = Form(""),
    escala: str = Form("1:64"),
    cor: str = Form(...),
    serie_colecao: str = Form(""),
    condicao: str = Form("Blister/Cartela Fechada"),
    codigo_barra_sku: str = Form(""),
    localizacao: str = Form(""),
    quantidade: int = Form(1),
    preco_compra: str = Form("0.0"),
    valor_estimado: str = Form("0.0"),
    observacoes: str = Form("")
):
    ano = int(ano_fabricacao) if ano_fabricacao and ano_fabricacao.isdigit() else None
    
    try:
        preco = float(preco_compra.replace(",", ".")) if preco_compra else 0.0
    except ValueError:
        preco = 0.0

    try:
        valor = float(valor_estimado.replace(",", ".")) if valor_estimado else 0.0
    except ValueError:
        valor = 0.0

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE carrinhos
            SET modelo_id = ?, ano_fabricacao = ?, escala = ?, cor = ?, serie_colecao = ?, condicao = ?,
                codigo_barra_sku = ?, localizacao = ?, quantidade = ?, preco_compra = ?, valor_estimado = ?, observacoes = ?
            WHERE id = ?
        """, (
            modelo_id, ano, escala.strip(), cor.strip(), serie_colecao.strip(), condicao.strip(),
            codigo_barra_sku.strip(), localizacao.strip(), max(0, quantidade), preco, valor, observacoes.strip(),
            id
        ))

    return RedirectResponse(url=f"/carrinhos/{id}?atualizado=true", status_code=303)

@router.delete("/{id}", response_class=HTMLResponse)
def excluir_carrinho(request: Request, id: int, view: str = "cards"):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM carrinhos WHERE id = ?", (id,))

        query = """
            SELECT c.*, 
                   m.nome as modelo_nome, m.tipo_carroceria, m.ano_lancamento as modelo_ano,
                   ma.id as marca_id, ma.nome as marca_nome, ma.pais_origem as marca_pais
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            ORDER BY c.id DESC
        """
        cursor.execute(query)
        carrinhos = cursor.fetchall()

    response = templates.TemplateResponse("carrinhos/partials/list.html", {
        "request": request,
        "carrinhos": carrinhos,
        "view": view
    })
    trigger_data = json.dumps({
        "showToast": {"value": f"Carrinho #{id} excluído com sucesso!", "type": "danger"},
        "stockChanged": True
    })
    response.headers["HX-Trigger"] = trigger_data
    return response
