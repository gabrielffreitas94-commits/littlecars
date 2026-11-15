from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import database
from routers import marcas, modelos, carrinhos, estoque

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa banco de dados SQLite e dados seed caso não existam
    database.init_db()
    yield

app = FastAPI(
    title="LittleCars - Gestão de Coleção de Carrinhos",
    description="Sistema web em FastAPI com front-end HTMX e CSS próprio para organização de carrinhos die-cast",
    version="1.0.0",
    lifespan=lifespan
)

# Monta arquivos estáticos (CSS próprio e HTMX local)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Registra os módulos de CRUD e Estoque
app.include_router(estoque.router)
app.include_router(carrinhos.router)
app.include_router(modelos.router)
app.include_router(marcas.router)

@app.get("/")
def raiz():
    # Redireciona a rota inicial diretamente para a página de estoque
    return RedirectResponse(url="/estoque", status_code=307)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
