import io
import csv
import json
from fastapi import APIRouter, Request, Form, Response, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from database import get_db

router = APIRouter(prefix="/estoque", tags=["estoque"])
templates = Jinja2Templates(directory="templates")

def get_estoque_metrics(cursor):
    cursor.execute("""
        SELECT 
            COALESCE(SUM(c.quantidade), 0) as total_carrinhos,
            COUNT(DISTINCT c.modelo_id) as total_modelos,
            COUNT(DISTINCT m.marca_id) as total_marcas,
            COALESCE(SUM(c.quantidade * c.valor_estimado), 0.0) as valor_total_estoque,
            COALESCE(SUM(CASE WHEN c.quantidade = 0 THEN 1 ELSE 0 END), 0) as total_esgotados,
            COALESCE(SUM(CASE WHEN c.quantidade = 1 THEN 1 ELSE 0 END), 0) as total_estoque_baixo
        FROM carrinhos c
        JOIN modelos m ON c.modelo_id = m.id
    """)
    row = cursor.fetchone()
    return {
        "total_carrinhos": row["total_carrinhos"],
        "total_modelos": row["total_modelos"],
        "total_marcas": row["total_marcas"],
        "valor_total_estoque": row["valor_total_estoque"],
        "total_esgotados": row["total_esgotados"],
        "total_estoque_baixo": row["total_estoque_baixo"],
    }

def get_carrinhos_estoque_query(busca="", marca_id="", status_estoque="", condicao="", localizacao="", ordenar_por=""):
    query = """
        SELECT c.*, 
               m.nome as modelo_nome, m.tipo_carroceria,
               ma.id as marca_id, ma.nome as marca_nome,
               (c.quantidade * c.valor_estimado) as valor_total_item
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

    if status_estoque == "esgotado":
        query += " AND c.quantidade = 0"
    elif status_estoque == "baixo":
        query += " AND c.quantidade = 1"
    elif status_estoque == "disponivel":
        query += " AND c.quantidade > 0"

    # Ordenação
    if ordenar_por == "qtd_desc":
        query += " ORDER BY c.quantidade DESC, m.nome ASC"
    elif ordenar_por == "qtd_asc":
        query += " ORDER BY c.quantidade ASC, m.nome ASC"
    elif ordenar_por == "valor_desc":
        query += " ORDER BY valor_total_item DESC"
    elif ordenar_por == "valor_asc":
        query += " ORDER BY valor_total_item ASC"
    else:
        query += " ORDER BY c.quantidade ASC, m.nome ASC"

    return query, params

@router.get("", response_class=HTMLResponse)
def index_estoque(
    request: Request,
    busca: str = "",
    marca_id: str = "",
    status_estoque: str = "",
    condicao: str = "",
    localizacao: str = "",
    ordenar_por: str = "qtd_asc"
):
    with get_db() as conn:
        cursor = conn.cursor()
        metrics = get_estoque_metrics(cursor)

        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

        cursor.execute("SELECT DISTINCT localizacao FROM carrinhos WHERE localizacao IS NOT NULL AND localizacao != '' ORDER BY localizacao ASC")
        localizacoes = [r["localizacao"] for r in cursor.fetchall()]

        query, params = get_carrinhos_estoque_query(busca, marca_id, status_estoque, condicao, localizacao, ordenar_por)
        cursor.execute(query, params)
        carrinhos = cursor.fetchall()

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx and ("busca" in request.query_params or "marca_id" in request.query_params or "status_estoque" in request.query_params or "condicao" in request.query_params or "localizacao" in request.query_params or "ordenar_por" in request.query_params):
        return templates.TemplateResponse("estoque/partials/table.html", {
            "request": request,
            "carrinhos": carrinhos
        })

    return templates.TemplateResponse("estoque/index.html", {
        "request": request,
        "metrics": metrics,
        "carrinhos": carrinhos,
        "marcas": marcas,
        "localizacoes": localizacoes,
        "busca": busca,
        "marca_id_selecionada": int(marca_id) if marca_id and marca_id.isdigit() else 0,
        "status_estoque_selecionado": status_estoque,
        "condicao_selecionada": condicao,
        "localizacao_selecionada": localizacao,
        "ordenar_por": ordenar_por,
        "active_page": "estoque",
        "total_itens_estoque": metrics["total_carrinhos"]
    })

@router.get("/metrics", response_class=HTMLResponse)
def get_metrics_partial(request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        metrics = get_estoque_metrics(cursor)
    return templates.TemplateResponse("estoque/partials/metrics.html", {
        "request": request,
        "metrics": metrics
    })

@router.get("/metrics/pill", response_class=HTMLResponse)
def get_metrics_pill():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM carrinhos")
        total = cursor.fetchone()["total"]
    return HTMLResponse(content=str(total))

@router.post("/{id}/increment", response_class=HTMLResponse)
def increment_estoque(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE carrinhos SET quantidade = quantidade + 1 WHERE id = ?", (id,))
        
        cursor.execute("""
            SELECT c.*, 
                   m.nome as modelo_nome, m.tipo_carroceria,
                   ma.id as marca_id, ma.nome as marca_nome,
                   (c.quantidade * c.valor_estimado) as valor_total_item
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            WHERE c.id = ?
        """, (id,))
        carrinho = cursor.fetchone()

    response = templates.TemplateResponse("estoque/partials/row.html", {
        "request": request,
        "c": carrinho
    })
    trigger_data = json.dumps({
        "showToast": {"value": f"+1 unidade adicionada ao estoque de {carrinho['modelo_nome']} ({carrinho['cor']})!"},
        "stockChanged": True
    })
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.post("/{id}/decrement", response_class=HTMLResponse)
def decrement_estoque(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        # Não deixa ficar menor que 0
        cursor.execute("UPDATE carrinhos SET quantidade = MAX(0, quantidade - 1) WHERE id = ?", (id,))
        
        cursor.execute("""
            SELECT c.*, 
                   m.nome as modelo_nome, m.tipo_carroceria,
                   ma.id as marca_id, ma.nome as marca_nome,
                   (c.quantidade * c.valor_estimado) as valor_total_item
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            WHERE c.id = ?
        """, (id,))
        carrinho = cursor.fetchone()

    response = templates.TemplateResponse("estoque/partials/row.html", {
        "request": request,
        "c": carrinho
    })
    trigger_data = json.dumps({
        "showToast": {"value": f"-1 unidade removida do estoque de {carrinho['modelo_nome']}!"},
        "stockChanged": True
    })
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.get("/modal/ajustar/{id}", response_class=HTMLResponse)
def modal_ajustar_estoque(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, m.nome as modelo_nome, ma.nome as marca_nome
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            WHERE c.id = ?
        """, (id,))
        carrinho = cursor.fetchone()
        if not carrinho:
            raise HTTPException(status_code=404, detail="Carrinho não encontrado")

    return templates.TemplateResponse("estoque/partials/adjust_modal.html", {
        "request": request,
        "carrinho": carrinho
    })

@router.post("/modal/ajustar/{id}", response_class=HTMLResponse)
def salvar_ajuste_estoque(
    request: Request,
    id: int,
    quantidade: int = Form(...),
    localizacao: str = Form(""),
    motivo: str = Form("")
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE carrinhos 
            SET quantidade = ?, localizacao = ?
            WHERE id = ?
        """, (max(0, quantidade), localizacao.strip(), id))

        cursor.execute("""
            SELECT c.*, 
                   m.nome as modelo_nome, m.tipo_carroceria,
                   ma.id as marca_id, ma.nome as marca_nome,
                   (c.quantidade * c.valor_estimado) as valor_total_item
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            WHERE c.id = ?
        """, (id,))
        carrinho = cursor.fetchone()

    response = templates.TemplateResponse("estoque/partials/row.html", {
        "request": request,
        "c": carrinho
    })
    motivo_txt = f" ({motivo})" if motivo else ""
    trigger_data = json.dumps({
        "showToast": {"value": f"Estoque de {carrinho['modelo_nome']} atualizado para {quantidade} un{motivo_txt}!"},
        "stockChanged": True
    })
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.get("/exportar")
def exportar_estoque_csv():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                c.id,
                ma.nome as marca,
                m.nome as modelo,
                m.tipo_carroceria,
                c.escala,
                c.ano_fabricacao,
                c.cor,
                c.serie_colecao,
                c.condicao,
                c.codigo_barra_sku,
                c.localizacao,
                c.quantidade,
                c.preco_compra,
                c.valor_estimado,
                (c.quantidade * c.valor_estimado) as valor_total
            FROM carrinhos c
            JOIN modelos m ON c.modelo_id = m.id
            JOIN marcas ma ON m.marca_id = ma.id
            ORDER BY ma.nome ASC, m.nome ASC
        """)
        linhas = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "ID", "Marca", "Modelo", "Carroceria", "Escala", "Ano Fabricacao",
        "Cor / Pintura", "Serie / Colecao", "Condicao", "SKU / Codigo",
        "Localizacao", "Quantidade em Estoque", "Preco Compra (R$)",
        "Valor Estimado (R$)", "Valor Total em Estoque (R$)"
    ])

    for row in linhas:
        writer.writerow([
            row["id"], row["marca"], row["modelo"], row["tipo_carroceria"], row["escala"],
            row["ano_fabricacao"], row["cor"], row["serie_colecao"], row["condicao"],
            row["codigo_barra_sku"], row["localizacao"], row["quantidade"],
            f"{row['preco_compra']:.2f}", f"{row['valor_estimado']:.2f}", f"{row['valor_total']:.2f}"
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=estoque_carrinhos.csv"}
    )
