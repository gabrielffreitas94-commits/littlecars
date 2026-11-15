import json
from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_db

router = APIRouter(prefix="/marcas", tags=["marcas"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
def listar_marcas(request: Request, busca: str = ""):
    with get_db() as conn:
        cursor = conn.cursor()
        if busca:
            query = """
                SELECT m.*, 
                       (SELECT COUNT(*) FROM modelos WHERE marca_id = m.id) as total_modelos,
                       (SELECT COUNT(*) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_carrinhos,
                       (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_exemplares
                FROM marcas m
                WHERE m.nome LIKE ? OR m.pais_origem LIKE ?
                ORDER BY m.nome ASC
            """
            cursor.execute(query, (f"%{busca}%", f"%{busca}%"))
        else:
            query = """
                SELECT m.*, 
                       (SELECT COUNT(*) FROM modelos WHERE marca_id = m.id) as total_modelos,
                       (SELECT COUNT(*) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_carrinhos,
                       (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_exemplares
                FROM marcas m
                ORDER BY m.nome ASC
            """
            cursor.execute(query)
        marcas = cursor.fetchall()

        # Contador para navbar
        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM carrinhos")
        total_estoque = cursor.fetchone()["total"]

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx and "busca" in request.query_params:
        return templates.TemplateResponse("marcas/partials/list.html", {
            "request": request,
            "marcas": marcas
        })

    return templates.TemplateResponse("marcas/index.html", {
        "request": request,
        "marcas": marcas,
        "busca": busca,
        "active_page": "marcas",
        "total_itens_estoque": total_estoque
    })

@router.get("/modal/novo", response_class=HTMLResponse)
def modal_nova_marca(request: Request):
    return templates.TemplateResponse("marcas/partials/form_modal.html", {
        "request": request,
        "marca": None,
        "titulo": "Adicionar Nova Marca"
    })

@router.get("/modal/editar/{id}", response_class=HTMLResponse)
def modal_editar_marca(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM marcas WHERE id = ?", (id,))
        marca = cursor.fetchone()
        if not marca:
            raise HTTPException(status_code=404, detail="Marca não encontrada")

    return templates.TemplateResponse("marcas/partials/form_modal.html", {
        "request": request,
        "marca": marca,
        "titulo": f"Editar Marca: {marca['nome']}"
    })

@router.post("", response_class=HTMLResponse)
def criar_marca(
    request: Request,
    nome: str = Form(...),
    pais_origem: str = Form(""),
    ano_fundacao: str = Form(""),
    descricao: str = Form(""),
    site_oficial: str = Form("")
):
    ano = int(ano_fundacao) if ano_fundacao and ano_fundacao.isdigit() else None
    
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO marcas (nome, pais_origem, ano_fundacao, descricao, site_oficial)
                VALUES (?, ?, ?, ?, ?)
            """, (nome.strip(), pais_origem.strip(), ano, descricao.strip(), site_oficial.strip()))
        except Exception as e:
            if "UNIQUE" in str(e):
                return HTMLResponse(
                    content=f"""
                    <div class="modal-body" style="color: #ef4444;">
                        <strong>Erro:</strong> Já existe uma marca cadastrada com o nome '{nome}'.
                        <button class="btn btn-secondary btn-sm" onclick="closeModal()" style="margin-top: 10px;">Fechar</button>
                    </div>
                    """,
                    status_code=400
                )
            raise e

        # Recarrega lista
        cursor.execute("""
            SELECT m.*, 
                   (SELECT COUNT(*) FROM modelos WHERE marca_id = m.id) as total_modelos,
                   (SELECT COUNT(*) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_carrinhos,
                   (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_exemplares
            FROM marcas m
            ORDER BY m.nome ASC
        """)
        marcas = cursor.fetchall()

    response = templates.TemplateResponse("marcas/partials/list.html", {
        "request": request,
        "marcas": marcas
    })
    trigger_data = json.dumps({"showToast": {"value": f"Marca '{nome}' cadastrada com sucesso!"}})
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.post("/{id}/editar", response_class=HTMLResponse)
def atualizar_marca(
    request: Request,
    id: int,
    nome: str = Form(...),
    pais_origem: str = Form(""),
    ano_fundacao: str = Form(""),
    descricao: str = Form(""),
    site_oficial: str = Form("")
):
    ano = int(ano_fundacao) if ano_fundacao and ano_fundacao.isdigit() else None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE marcas
            SET nome = ?, pais_origem = ?, ano_fundacao = ?, descricao = ?, site_oficial = ?
            WHERE id = ?
        """, (nome.strip(), pais_origem.strip(), ano, descricao.strip(), site_oficial.strip(), id))

        cursor.execute("""
            SELECT m.*, 
                   (SELECT COUNT(*) FROM modelos WHERE marca_id = m.id) as total_modelos,
                   (SELECT COUNT(*) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_carrinhos,
                   (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_exemplares
            FROM marcas m
            ORDER BY m.nome ASC
        """)
        marcas = cursor.fetchall()

    response = templates.TemplateResponse("marcas/partials/list.html", {
        "request": request,
        "marcas": marcas
    })
    trigger_data = json.dumps({"showToast": {"value": f"Marca '{nome}' atualizada com sucesso!"}})
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.delete("/{id}", response_class=HTMLResponse)
def excluir_marca(request: Request, id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM marcas WHERE id = ?", (id,))
        marca = cursor.fetchone()
        nome_marca = marca["nome"] if marca else f"ID {id}"

        cursor.execute("DELETE FROM marcas WHERE id = ?", (id,))

        cursor.execute("""
            SELECT m.*, 
                   (SELECT COUNT(*) FROM modelos WHERE marca_id = m.id) as total_modelos,
                   (SELECT COUNT(*) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_carrinhos,
                   (SELECT COALESCE(SUM(c.quantidade), 0) FROM carrinhos c JOIN modelos mod ON c.modelo_id = mod.id WHERE mod.marca_id = m.id) as total_exemplares
            FROM marcas m
            ORDER BY m.nome ASC
        """)
        marcas = cursor.fetchall()

    response = templates.TemplateResponse("marcas/partials/list.html", {
        "request": request,
        "marcas": marcas
    })
    trigger_data = json.dumps({
        "showToast": {"value": f"Marca '{nome_marca}' e dependências excluídas!", "type": "danger"},
        "stockChanged": True
    })
    response.headers["HX-Trigger"] = trigger_data
    return response

@router.get("/options", response_class=HTMLResponse)
def options_marcas(selected_id: int = 0):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas = cursor.fetchall()

    html = '<option value="">-- Selecione uma Marca --</option>'
    for m in marcas:
        sel = "selected" if m["id"] == selected_id else ""
        html += f'<option value="{m["id"]}" {sel}>{m["nome"]}</option>'
    return HTMLResponse(content=html)
