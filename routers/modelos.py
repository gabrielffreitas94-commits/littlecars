import json
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_db

router = APIRouter(prefix="/modelos", tags=["modelos"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
def listar_modelos(request: Request, busca: str = "", marca_id: str = ""):
    with get_db() as conn:
        cursor = conn.cursor()

        # Marcas para o filtro
        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

        # Consulta com joins e contadores
        query = """
            SELECT m.*, ma.nome as marca_nome,
                   (SELECT COUNT(*) FROM carrinhos c WHERE c.modelo_id = m.id) as total_carrinhos,
                   (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c WHERE c.modelo_id = m.id) as total_exemplares
            FROM modelos m
            JOIN marcas ma ON m.marca_id = ma.id
            WHERE 1=1
        """
        params = []

        if busca:
            query += " AND (m.nome LIKE ? OR m.tipo_carroceria LIKE ? OR ma.nome LIKE ?)"
            params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])

        if marca_id and marca_id.isdigit():
            query += " AND m.marca_id = ?"
            params.append(int(marca_id))

        query += " ORDER BY ma.nome ASC, m.nome ASC"

        cursor.execute(query, params)
        modelos = cursor.fetchall()

        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM carrinhos")
        total_estoque = cursor.fetchone()["total"]

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx and ("busca" in request.query_params or "marca_id" in request.query_params):
        return templates.TemplateResponse("modelos/partials/list.html", {
            "request": request,
            "modelos": modelos
        })

    return templates.TemplateResponse("modelos/index.html", {
        "request": request,
        "modelos": modelos,
        "marcas": marcas,
        "busca": busca,
        "marca_id_selecionada": int(marca_id) if marca_id and marca_id.isdigit() else 0,
        "active_page": "modelos",
        "total_itens_estoque": total_estoque
    })

@router.get("/modal/novo", response_class=HTMLResponse)
def modal_novo_modelo(request: Request, default_marca_id: int = 0):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

    return templates.TemplateResponse("modelos/partials/form_modal.html", {
        "request": request,
        "modelo": None,
        "marcas": marcas,
        "default_marca_id": default_marca_id,
        "titulo": "Adicionar Novo Modelo"
    })

@router.get("/modal/editar/{id}", response_class=HTMLResponse)
def modal_editar_modelo(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM modelos WHERE id = ?", (id,))
        modelo = cursor.fetchone()
        if not modelo:
            raise HTTPException(status_code=404, detail="Modelo não encontrado")

        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

    return templates.TemplateResponse("modelos/partials/form_modal.html", {
        "request": request,
        "modelo": modelo,
        "marcas": marcas,
        "default_marca_id": modelo["marca_id"],
        "titulo": f"Editar Modelo: {modelo['nome']}"
    })

@router.post("", response_class=HTMLResponse)
def criar_modelo(
    request: Request,
    marca_id: int = Form(...),
    nome: str = Form(...),
    tipo_carroceria: str = Form(""),
    ano_lancamento: str = Form(""),
    descricao: str = Form("")
):
    ano = int(ano_lancamento) if ano_lancamento and ano_lancamento.isdigit() else None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO modelos (marca_id, nome, tipo_carroceria, ano_lancamento, descricao)
            VALUES (?, ?, ?, ?, ?)
        """, (marca_id, nome.strip(), tipo_carroceria.strip(), ano, descricao.strip()))

        cursor.execute("""
            SELECT m.*, ma.nome as marca_nome,
                   (SELECT COUNT(*) FROM carrinhos c WHERE c.modelo_id = m.id) as total_carrinhos,
                   (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c WHERE c.modelo_id = m.id) as total_exemplares
            FROM modelos m
            JOIN marcas ma ON m.marca_id = ma.id
            ORDER BY ma.nome ASC, m.nome ASC
        """)
        modelos = cursor.fetchall()

    response = templates.TemplateResponse("modelos/partials/list.html", {
        "request": request,
        "modelos": modelos
    })
    trigger_data = json.dumps({"showToast": {"value": f"Modelo '{nome}' cadastrado com sucesso!"}})
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.post("/{id}/editar", response_class=HTMLResponse)
def atualizar_modelo(
    request: Request,
    id: int,
    marca_id: int = Form(...),
    nome: str = Form(...),
    tipo_carroceria: str = Form(""),
    ano_lancamento: str = Form(""),
    descricao: str = Form("")
):
    ano = int(ano_lancamento) if ano_lancamento and ano_lancamento.isdigit() else None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE modelos
            SET marca_id = ?, nome = ?, tipo_carroceria = ?, ano_lancamento = ?, descricao = ?
            WHERE id = ?
        """, (marca_id, nome.strip(), tipo_carroceria.strip(), ano, descricao.strip(), id))

        cursor.execute("""
            SELECT m.*, ma.nome as marca_nome,
                   (SELECT COUNT(*) FROM carrinhos c WHERE c.modelo_id = m.id) as total_carrinhos,
                   (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c WHERE c.modelo_id = m.id) as total_exemplares
            FROM modelos m
            JOIN marcas ma ON m.marca_id = ma.id
            ORDER BY ma.nome ASC, m.nome ASC
        """)
        modelos = cursor.fetchall()

    response = templates.TemplateResponse("modelos/partials/list.html", {
        "request": request,
        "modelos": modelos
    })
    trigger_data = json.dumps({"showToast": {"value": f"Modelo '{nome}' atualizado com sucesso!"}})
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.delete("/{id}", response_class=HTMLResponse)
def excluir_modelo(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM modelos WHERE id = ?", (id,))
        modelo = cursor.fetchone()
        nome_modelo = modelo["nome"] if modelo else f"ID {id}"

        cursor.execute("DELETE FROM modelos WHERE id = ?", (id,))

        cursor.execute("""
            SELECT m.*, ma.nome as marca_nome,
                   (SELECT COUNT(*) FROM carrinhos c WHERE c.modelo_id = m.id) as total_carrinhos,
                   (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c WHERE c.modelo_id = m.id) as total_exemplares
            FROM modelos m
            JOIN marcas ma ON m.marca_id = ma.id
            ORDER BY ma.nome ASC, m.nome ASC
        """)
        modelos = cursor.fetchall()

    response = templates.TemplateResponse("modelos/partials/list.html", {
        "request": request,
        "modelos": modelos
    })
    trigger_data = json.dumps({
        "showToast": {"value": f"Modelo '{nome_modelo}' e itens vinculados foram excluídos!", "type": "danger"},
        "stockChanged": True
    })
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.get("/options", response_class=HTMLResponse)
def options_modelos(marca_id: str = "", selected_id: int = 0):
    with get_db() as conn:
        cursor = conn.cursor()
        if marca_id and marca_id.isdigit() and int(marca_id) > 0:
            cursor.execute("SELECT id, nome, tipo_carroceria FROM modelos WHERE marca_id = ? ORDER BY nome ASC", (int(marca_id),))
        else:
            cursor.execute("""
                SELECT m.id, m.nome, m.tipo_carroceria, ma.nome as marca_nome 
                FROM modelos m 
                JOIN marcas ma ON m.marca_id = ma.id 
                ORDER BY ma.nome ASC, m.nome ASC
            """)
        modelos = cursor.fetchall()

    html = '<option value="">-- Selecione um Modelo --</option>'
    for m in modelos:
        sel = "selected" if m["id"] == selected_id else ""
        marca_label = f"[{m['marca_nome']}] " if "marca_nome" in m.keys() else ""
        carroceria = f" ({m['tipo_carroceria']})" if m['tipo_carroceria'] else ""
        html += f'<option value="{m["id"]}" {sel}>{marca_label}{m["nome"]}{carroceria}</option>'
    return HTMLResponse(content=html)
