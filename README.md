# 🏎️ LittleCars &mdash; Gestão de Coleção de Carrinhos de Brinquedo

Um aplicativo web moderno feito em **FastAPI**, com front-end renderizado diretamente pelo Python utilizando **HTMX** para interatividade fluida e dinâmica sem recarregamento de página, e estilizado com **CSS 100% próprio** (sem Tailwind, Bootstrap ou qualquer biblioteca externa de estilos).

---

## 🌟 Funcionalidades

1. **📦 Página de Estoque**:
   - Painel com 5 cartões de indicadores (KPIs): Total de carrinhos físicos, modelos distintos, marcas ativas, valor total estimado do acervo e alerta de estoque crítico (zerados e última unidade).
   - Filtros dinâmicos em tempo real com HTMX (busca por texto, marca, status de estoque, condição, localização e ordenação por quantidade ou valor).
   - Botões instantâneos de passo (`+` e `−`) para aumentar ou diminuir unidades diretamente na tabela.
   - Modal de ajuste rápido de quantidade, localização e motivo da alteração.
   - Exportação do inventário completo para planilha em formato **CSV**.

2. **🏭 CRUD de Marcas**:
   - Cadastro, edição, listagem e exclusão de marcas fabricantes (ex.: *Hot Wheels*, *Matchbox*, *Tomica*, *Mini GT*, *Majorette*).
   - Informações: Nome da marca, país de origem, ano de fundação, site oficial e história/descrição.
   - Contadores automáticos de modelos cadastrados e itens em estoque por marca.

3. **🏷️ CRUD de Modelos**:
   - Cadastro, edição, listagem e exclusão de modelos de veículos associados às marcas.
   - Informações: Nome do modelo (ex.: *'67 Camaro*, *Nissan Skyline GT-R R34*, *Porsche 911 GT3 RS*), marca vinculada, tipo de carroceria (Muscle Car, Esportivo, SUV, etc.), ano de lançamento real e curiosidades.
   - Dropdown dinâmico que carrega automaticamente os modelos da marca selecionada.

4. **🚗 CRUD de Carrinhos (Itens Físicos da Coleção)**:
   - Gerenciamento detalhado de cada exemplar do colecionador.
   - Informações: Escala (*1:64, 1:43, 1:32, etc.*), cor e decorações, série/linha colecionável (*Mainline, Premium, Retro, Boulevard*), estado de conservação (*Blister lacrado, loose impecável, etc.*), código SKU/chassi, local de armazenamento (*Estante, gaveta, maleta*), quantidade em estoque, preço pago e valor de mercado estimado.
   - Alternância de visualização entre **Galeria em Cards** e **Tabela Completa**.
   - Página de detalhes dedicada com ficha técnica completa e análise de valorização patrimonial.

5. **🎨 Design & CSS Próprio**:
   - Paleta escura inspirada em garagens esportivas e vitrines de colecionador.
   - Modais interativos, badges de status estilizados e toasts flutuantes para feedback instantâneo de ações.
   - Responsivo para computadores, tablets e smartphones.

---

## 🚀 Como Executar

O ambiente já possui as dependências instaladas. Para iniciar o servidor de desenvolvimento, execute no terminal:

```bash
python main.py
```

Ou usando o Uvicorn diretamente:

```bash
python -m uvicorn main:app --reload --port 8000
```

Abra o navegador no endereço: **http://127.0.0.1:8000**
