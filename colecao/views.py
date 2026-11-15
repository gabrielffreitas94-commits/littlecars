import io
import csv
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, F, Q, ExpressionWrapper, FloatField, IntegerField, Case, When, Value
from django.db import IntegrityError

from .models import Marca, Modelo, Carrinho

# ============================================================
# ESTOQUE
# ============================================================

def calcular_metricas_estoque():
    agg = Carrinho.objects.aggregate(
        total_carrinhos=Sum('quantidade', default=0),
        total_modelos=Count('modelo_id', distinct=True),
        total_marcas=Count('modelo__marca_id', distinct=True),
        valor_total_estoque=Sum(
            ExpressionWrapper(F('quantidade') * F('valor_estimado'), output_field=FloatField()),
            default=0.0
        ),
        total_esgotados=Count(Case(When(quantidade=0, then=Value(1)), output_field=IntegerField())),
        total_estoque_baixo=Count(Case(When(quantidade=1, then=Value(1)), output_field=IntegerField()))
    )
    total_esgotados = agg['total_esgotados'] or 0
    total_estoque_baixo = agg['total_estoque_baixo'] or 0
    return {
        "total_carrinhos": agg['total_carrinhos'] or 0,
        "total_modelos": agg['total_modelos'] or 0,
        "total_marcas": agg['total_marcas'] or 0,
        "valor_total_estoque": agg['valor_total_estoque'] or 0.0,
        "total_esgotados": total_esgotados,
        "total_estoque_baixo": total_estoque_baixo,
        "total_critico": total_esgotados + total_estoque_baixo,
    }

def filtrar_carrinhos_estoque(busca="", marca_id="", status_estoque="", condicao="", localizacao="", ordenar_por="qtd_asc"):
    qs = Carrinho.objects.select_related('modelo', 'modelo__marca').annotate(
        valor_total_item=ExpressionWrapper(F('quantidade') * F('valor_estimado'), output_field=FloatField())
    )

    if busca:
        qs = qs.filter(
            Q(modelo__nome__icontains=busca) |
            Q(cor__icontains=busca) |
            Q(serie_colecao__icontains=busca) |
            Q(codigo_barra_sku__icontains=busca) |
            Q(modelo__marca__nome__icontains=busca)
        )

    if marca_id and marca_id.isdigit():
        qs = qs.filter(modelo__marca_id=int(marca_id))

    if condicao:
        qs = qs.filter(condicao=condicao)

    if localizacao:
        qs = qs.filter(localizacao=localizacao)

    if status_estoque == "esgotado":
        qs = qs.filter(quantidade=0)
    elif status_estoque == "baixo":
        qs = qs.filter(quantidade=1)
    elif status_estoque == "disponivel":
        qs = qs.filter(quantidade__gt=0)

    # Ordenação
    if ordenar_por == "qtd_desc":
        qs = qs.order_by('-quantidade', 'modelo__nome')
    elif ordenar_por == "qtd_asc":
        qs = qs.order_by('quantidade', 'modelo__nome')
    elif ordenar_por == "valor_desc":
        qs = qs.order_by('-valor_total_item')
    elif ordenar_por == "valor_asc":
        qs = qs.order_by('valor_total_item')
    else:
        qs = qs.order_by('quantidade', 'modelo__nome')

    return qs

def estoque_view(request):
    busca = request.GET.get('busca', '').strip()
    marca_id = request.GET.get('marca_id', '').strip()
    status_estoque = request.GET.get('status_estoque', '').strip()
    condicao = request.GET.get('condicao', '').strip()
    localizacao = request.GET.get('localizacao', '').strip()
    ordenar_por = request.GET.get('ordenar_por', 'qtd_asc').strip()

    carrinhos = filtrar_carrinhos_estoque(busca, marca_id, status_estoque, condicao, localizacao, ordenar_por)

    is_htmx = request.headers.get('HX-Request') == 'true'
    is_filtering = any(k in request.GET for k in ['busca', 'marca_id', 'status_estoque', 'condicao', 'localizacao', 'ordenar_por'])

    if is_htmx and is_filtering:
        return render(request, 'estoque/partials/table.html', {
            'carrinhos': carrinhos
        })

    metrics = calcular_metricas_estoque()
    marcas = Marca.objects.all().order_by('nome')
    localizacoes = (
        Carrinho.objects.exclude(localizacao__isnull=True)
        .exclude(localizacao__exact='')
        .values_list('localizacao', flat=True)
        .distinct()
        .order_by('localizacao')
    )

    return render(request, 'estoque/index.html', {
        'metrics': metrics,
        'carrinhos': carrinhos,
        'marcas': marcas,
        'localizacoes': localizacoes,
        'busca': busca,
        'marca_id_selecionada': int(marca_id) if marca_id.isdigit() else 0,
        'status_estoque_selecionado': status_estoque,
        'condicao_selecionada': condicao,
        'localizacao_selecionada': localizacao,
        'ordenar_por': ordenar_por,
        'active_page': 'estoque',
    })

def get_metrics_partial(request):
    metrics = calcular_metricas_estoque()
    return render(request, 'estoque/partials/metrics.html', {
        'metrics': metrics
    })

def get_metrics_pill(request):
    total = Carrinho.objects.aggregate(t=Sum('quantidade'))['t'] or 0
    return HttpResponse(str(total))

@require_http_methods(["POST"])
def increment_estoque(request, id):
    carrinho = get_object_or_404(
        Carrinho.objects.select_related('modelo', 'modelo__marca').annotate(
            valor_total_item=ExpressionWrapper(F('quantidade') * F('valor_estimado'), output_field=FloatField())
        ),
        id=id
    )
    carrinho.quantidade += 1
    carrinho.save(update_fields=['quantidade'])
    carrinho.valor_total_item = carrinho.quantidade * carrinho.valor_estimado

    response = render(request, 'estoque/partials/row.html', {'c': carrinho})
    trigger_data = json.dumps({
        "showToast": {"value": f"+1 unidade adicionada ao estoque de {carrinho.modelo.nome} ({carrinho.cor})!"},
        "stockChanged": True
    })
    response['HX-Trigger'] = trigger_data
    return response

@require_http_methods(["POST"])
def decrement_estoque(request, id):
    carrinho = get_object_or_404(
        Carrinho.objects.select_related('modelo', 'modelo__marca').annotate(
            valor_total_item=ExpressionWrapper(F('quantidade') * F('valor_estimado'), output_field=FloatField())
        ),
        id=id
    )
    carrinho.quantidade = max(0, carrinho.quantidade - 1)
    carrinho.save(update_fields=['quantidade'])
    carrinho.valor_total_item = carrinho.quantidade * carrinho.valor_estimado

    response = render(request, 'estoque/partials/row.html', {'c': carrinho})
    trigger_data = json.dumps({
        "showToast": {"value": f"-1 unidade removida do estoque de {carrinho.modelo.nome}!"},
        "stockChanged": True
    })
    response['HX-Trigger'] = trigger_data
    return response

def ajustar_estoque_modal_view(request, id):
    if request.method == 'POST':
        carrinho = get_object_or_404(Carrinho.objects.select_related('modelo', 'modelo__marca'), id=id)
        qtd_raw = request.POST.get('quantidade', '0')
        localizacao = request.POST.get('localizacao', '').strip()
        motivo = request.POST.get('motivo', '').strip()

        try:
            qtd = max(0, int(qtd_raw))
        except ValueError:
            qtd = 0

        carrinho.quantidade = qtd
        carrinho.localizacao = localizacao
        carrinho.save(update_fields=['quantidade', 'localizacao'])
        carrinho.valor_total_item = carrinho.quantidade * carrinho.valor_estimado

        response = render(request, 'estoque/partials/row.html', {'c': carrinho})
        motivo_txt = f" ({motivo})" if motivo else ""
        trigger_data = json.dumps({
            "showToast": {"value": f"Estoque de {carrinho.modelo.nome} atualizado para {qtd} un{motivo_txt}!"},
            "stockChanged": True
        })
        response['HX-Trigger'] = trigger_data
        return response

    carrinho = get_object_or_404(Carrinho.objects.select_related('modelo', 'modelo__marca'), id=id)
    return render(request, 'estoque/partials/adjust_modal.html', {'carrinho': carrinho})

def exportar_estoque_csv(request):
    carrinhos = Carrinho.objects.select_related('modelo', 'modelo__marca').order_by('modelo__marca__nome', 'modelo__nome')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="estoque_carrinhos.csv"'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        "ID", "Marca", "Modelo", "Carroceria", "Escala", "Ano Fabricacao",
        "Cor / Pintura", "Serie / Colecao", "Condicao", "SKU / Codigo",
        "Localizacao", "Quantidade em Estoque", "Preco Compra (R$)",
        "Valor Estimado (R$)", "Valor Total em Estoque (R$)"
    ])

    for c in carrinhos:
        valor_total = (c.quantidade or 0) * (c.valor_estimado or 0.0)
        writer.writerow([
            c.id,
            c.modelo.marca.nome,
            c.modelo.nome,
            c.modelo.tipo_carroceria or '',
            c.escala or '',
            c.ano_fabricacao or '',
            c.cor,
            c.serie_colecao or '',
            c.condicao or '',
            c.codigo_barra_sku or '',
            c.localizacao or '',
            c.quantidade,
            f"{c.preco_compra:.2f}",
            f"{c.valor_estimado:.2f}",
            f"{valor_total:.2f}"
        ])

    return response

# ============================================================
# MARCAS
# ============================================================

def get_marcas_annotated(busca=""):
    qs = Marca.objects.annotate(
        total_modelos=Count('modelos', distinct=True),
        total_carrinhos=Count('modelos__carrinhos', distinct=True),
        total_exemplares=Sum('modelos__carrinhos__quantidade', default=0)
    ).order_by('nome')

    if busca:
        qs = qs.filter(Q(nome__icontains=busca) | Q(pais_origem__icontains=busca))
    return qs

def marcas_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        pais_origem = request.POST.get('pais_origem', '').strip()
        ano_fundacao_raw = request.POST.get('ano_fundacao', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        site_oficial = request.POST.get('site_oficial', '').strip()

        ano = int(ano_fundacao_raw) if ano_fundacao_raw.isdigit() else None

        try:
            Marca.objects.create(
                nome=nome,
                pais_origem=pais_origem,
                ano_fundacao=ano,
                descricao=descricao,
                site_oficial=site_oficial
            )
        except IntegrityError:
            return HttpResponse(
                f"""
                <div class="modal-body" style="color: #ef4444;">
                    <strong>Erro:</strong> Já existe uma marca cadastrada com o nome '{nome}'.
                    <button class="btn btn-secondary btn-sm" onclick="closeModal()" style="margin-top: 10px;">Fechar</button>
                </div>
                """,
                status=400
            )

        marcas = get_marcas_annotated()
        response = render(request, 'marcas/partials/list.html', {'marcas': marcas})
        trigger_data = json.dumps({"showToast": {"value": f"Marca '{nome}' cadastrada com sucesso!"}})
        response['HX-Trigger'] = trigger_data
        return response

    busca = request.GET.get('busca', '').strip()
    marcas = get_marcas_annotated(busca)

    is_htmx = request.headers.get('HX-Request') == 'true'
    if is_htmx and 'busca' in request.GET:
        return render(request, 'marcas/partials/list.html', {'marcas': marcas})

    return render(request, 'marcas/index.html', {
        'marcas': marcas,
        'busca': busca,
        'active_page': 'marcas'
    })

def modal_nova_marca(request):
    return render(request, 'marcas/partials/form_modal.html', {
        'marca': None,
        'titulo': "Adicionar Nova Marca"
    })

def modal_editar_marca(request, id):
    marca = get_object_or_404(Marca, id=id)
    return render(request, 'marcas/partials/form_modal.html', {
        'marca': marca,
        'titulo': f"Editar Marca: {marca.nome}"
    })

@require_http_methods(["POST"])
def atualizar_marca(request, id):
    marca = get_object_or_404(Marca, id=id)
    nome = request.POST.get('nome', '').strip()
    pais_origem = request.POST.get('pais_origem', '').strip()
    ano_fundacao_raw = request.POST.get('ano_fundacao', '').strip()
    descricao = request.POST.get('descricao', '').strip()
    site_oficial = request.POST.get('site_oficial', '').strip()

    ano = int(ano_fundacao_raw) if ano_fundacao_raw.isdigit() else None

    marca.nome = nome
    marca.pais_origem = pais_origem
    marca.ano_fundacao = ano
    marca.descricao = descricao
    marca.site_oficial = site_oficial
    marca.save()

    marcas = get_marcas_annotated()
    response = render(request, 'marcas/partials/list.html', {'marcas': marcas})
    trigger_data = json.dumps({"showToast": {"value": f"Marca '{nome}' atualizada com sucesso!"}})
    response['HX-Trigger'] = trigger_data
    return response

@require_http_methods(["DELETE"])
def marca_detail_delete_view(request, id):
    marca = get_object_or_404(Marca, id=id)
    nome_marca = marca.nome
    marca.delete()

    marcas = get_marcas_annotated()
    response = render(request, 'marcas/partials/list.html', {'marcas': marcas})
    trigger_data = json.dumps({
        "showToast": {"value": f"Marca '{nome_marca}' e dependências excluídas!", "type": "danger"},
        "stockChanged": True
    })
    response['HX-Trigger'] = trigger_data
    return response

def options_marcas(request):
    selected_id_raw = request.GET.get('selected_id', '0')
    selected_id = int(selected_id_raw) if selected_id_raw.isdigit() else 0
    marcas = Marca.objects.all().order_by('nome')

    html = '<option value="">-- Selecione uma Marca --</option>'
    for m in marcas:
        sel = "selected" if m.id == selected_id else ""
        html += f'<option value="{m.id}" {sel}>{m.nome}</option>'
    return HttpResponse(html)

# ============================================================
# MODELOS
# ============================================================

def get_modelos_annotated(busca="", marca_id=""):
    qs = Modelo.objects.select_related('marca').annotate(
        total_carrinhos=Count('carrinhos', distinct=True),
        total_exemplares=Sum('carrinhos__quantidade', default=0)
    ).order_by('marca__nome', 'nome')

    if busca:
        qs = qs.filter(
            Q(nome__icontains=busca) |
            Q(tipo_carroceria__icontains=busca) |
            Q(marca__nome__icontains=busca)
        )

    if marca_id and marca_id.isdigit():
        qs = qs.filter(marca_id=int(marca_id))

    return qs

def modelos_view(request):
    if request.method == 'POST':
        marca_id = request.POST.get('marca_id')
        nome = request.POST.get('nome', '').strip()
        tipo_carroceria = request.POST.get('tipo_carroceria', '').strip()
        ano_lancamento_raw = request.POST.get('ano_lancamento', '').strip()
        descricao = request.POST.get('descricao', '').strip()

        ano = int(ano_lancamento_raw) if ano_lancamento_raw.isdigit() else None
        marca = get_object_or_404(Marca, id=marca_id)

        Modelo.objects.create(
            marca=marca,
            nome=nome,
            tipo_carroceria=tipo_carroceria,
            ano_lancamento=ano,
            descricao=descricao
        )

        modelos = get_modelos_annotated()
        response = render(request, 'modelos/partials/list.html', {'modelos': modelos})
        trigger_data = json.dumps({"showToast": {"value": f"Modelo '{nome}' cadastrado com sucesso!"}})
        response['HX-Trigger'] = trigger_data
        return response

    busca = request.GET.get('busca', '').strip()
    marca_id = request.GET.get('marca_id', '').strip()
    modelos = get_modelos_annotated(busca, marca_id)

    is_htmx = request.headers.get('HX-Request') == 'true'
    if is_htmx and ('busca' in request.GET or 'marca_id' in request.GET):
        return render(request, 'modelos/partials/list.html', {'modelos': modelos})

    marcas = Marca.objects.all().order_by('nome')
    return render(request, 'modelos/index.html', {
        'modelos': modelos,
        'marcas': marcas,
        'busca': busca,
        'marca_id_selecionada': int(marca_id) if marca_id.isdigit() else 0,
        'active_page': 'modelos'
    })

def modal_novo_modelo(request):
    default_marca_id_raw = request.GET.get('default_marca_id', '0')
    default_marca_id = int(default_marca_id_raw) if default_marca_id_raw.isdigit() else 0
    marcas = Marca.objects.all().order_by('nome')
    return render(request, 'modelos/partials/form_modal.html', {
        'modelo': None,
        'marcas': marcas,
        'default_marca_id': default_marca_id,
        'titulo': "Adicionar Novo Modelo"
    })

def modal_editar_modelo(request, id):
    modelo = get_object_or_404(Modelo, id=id)
    marcas = Marca.objects.all().order_by('nome')
    return render(request, 'modelos/partials/form_modal.html', {
        'modelo': modelo,
        'marcas': marcas,
        'default_marca_id': modelo.marca_id,
        'titulo': f"Editar Modelo: {modelo.nome}"
    })

@require_http_methods(["POST"])
def atualizar_modelo(request, id):
    modelo = get_object_or_404(Modelo, id=id)
    marca_id = request.POST.get('marca_id')
    nome = request.POST.get('nome', '').strip()
    tipo_carroceria = request.POST.get('tipo_carroceria', '').strip()
    ano_lancamento_raw = request.POST.get('ano_lancamento', '').strip()
    descricao = request.POST.get('descricao', '').strip()

    ano = int(ano_lancamento_raw) if ano_lancamento_raw.isdigit() else None
    marca = get_object_or_404(Marca, id=marca_id)

    modelo.marca = marca
    modelo.nome = nome
    modelo.tipo_carroceria = tipo_carroceria
    modelo.ano_lancamento = ano
    modelo.descricao = descricao
    modelo.save()

    modelos = get_modelos_annotated()
    response = render(request, 'modelos/partials/list.html', {'modelos': modelos})
    trigger_data = json.dumps({"showToast": {"value": f"Modelo '{nome}' atualizado com sucesso!"}})
    response['HX-Trigger'] = trigger_data
    return response

@require_http_methods(["DELETE"])
def modelo_detail_delete_view(request, id):
    modelo = get_object_or_404(Modelo, id=id)
    nome_modelo = modelo.nome
    modelo.delete()

    modelos = get_modelos_annotated()
    response = render(request, 'modelos/partials/list.html', {'modelos': modelos})
    trigger_data = json.dumps({
        "showToast": {"value": f"Modelo '{nome_modelo}' e itens vinculados foram excluídos!", "type": "danger"},
        "stockChanged": True
    })
    response['HX-Trigger'] = trigger_data
    return response

def options_modelos(request):
    marca_id_raw = request.GET.get('marca_id', '').strip()
    selected_id_raw = request.GET.get('selected_id', '0').strip()
    selected_id = int(selected_id_raw) if selected_id_raw.isdigit() else 0

    if marca_id_raw and marca_id_raw.isdigit() and int(marca_id_raw) > 0:
        modelos = Modelo.objects.filter(marca_id=int(marca_id_raw)).order_by('nome')
        has_marca_prefix = False
    else:
        modelos = Modelo.objects.select_related('marca').order_by('marca__nome', 'nome')
        has_marca_prefix = True

    html = '<option value="">-- Selecione um Modelo --</option>'
    for m in modelos:
        sel = "selected" if m.id == selected_id else ""
        marca_label = f"[{m.marca.nome}] " if has_marca_prefix else ""
        carroceria = f" ({m.tipo_carroceria})" if m.tipo_carroceria else ""
        html += f'<option value="{m.id}" {sel}>{marca_label}{m.nome}{carroceria}</option>'
    return HttpResponse(html)

# ============================================================
# CARRINHOS
# ============================================================

def get_carrinhos_qs(busca="", marca_id="", condicao="", localizacao=""):
    qs = Carrinho.objects.select_related('modelo', 'modelo__marca').order_by('-id')

    if busca:
        qs = qs.filter(
            Q(modelo__nome__icontains=busca) |
            Q(cor__icontains=busca) |
            Q(serie_colecao__icontains=busca) |
            Q(codigo_barra_sku__icontains=busca) |
            Q(modelo__marca__nome__icontains=busca)
        )

    if marca_id and marca_id.isdigit():
        qs = qs.filter(modelo__marca_id=int(marca_id))

    if condicao:
        qs = qs.filter(condicao=condicao)

    if localizacao:
        qs = qs.filter(localizacao=localizacao)

    return qs

def carrinhos_view(request):
    if request.method == 'POST':
        modelo_id = request.POST.get('modelo_id')
        modelo = get_object_or_404(Modelo, id=modelo_id)

        ano_raw = request.POST.get('ano_fabricacao', '').strip()
        ano = int(ano_raw) if ano_raw.isdigit() else None

        escala = request.POST.get('escala', '1:64').strip()
        cor = request.POST.get('cor', '').strip()
        serie_colecao = request.POST.get('serie_colecao', '').strip()
        condicao = request.POST.get('condicao', 'Blister/Cartela Fechada').strip()
        codigo_barra_sku = request.POST.get('codigo_barra_sku', '').strip()
        localizacao = request.POST.get('localizacao', '').strip()
        
        qtd_raw = request.POST.get('quantidade', '1')
        try:
            quantidade = max(0, int(qtd_raw))
        except ValueError:
            quantidade = 1

        preco_raw = request.POST.get('preco_compra', '0.0').replace(',', '.')
        try:
            preco_compra = float(preco_raw)
        except ValueError:
            preco_compra = 0.0

        valor_raw = request.POST.get('valor_estimado', '0.0').replace(',', '.')
        try:
            valor_estimado = float(valor_raw)
        except ValueError:
            valor_estimado = 0.0

        observacoes = request.POST.get('observacoes', '').strip()

        carrinho = Carrinho.objects.create(
            modelo=modelo,
            ano_fabricacao=ano,
            escala=escala,
            cor=cor,
            serie_colecao=serie_colecao,
            condicao=condicao,
            codigo_barra_sku=codigo_barra_sku,
            localizacao=localizacao,
            quantidade=quantidade,
            preco_compra=preco_compra,
            valor_estimado=valor_estimado,
            observacoes=observacoes
        )

        return redirect(f"/carrinhos/{carrinho.id}?cadastrado=true")

    busca = request.GET.get('busca', '').strip()
    marca_id = request.GET.get('marca_id', '').strip()
    condicao = request.GET.get('condicao', '').strip()
    localizacao = request.GET.get('localizacao', '').strip()
    view = request.GET.get('view', 'cards').strip()

    carrinhos = get_carrinhos_qs(busca, marca_id, condicao, localizacao)

    is_htmx = request.headers.get('HX-Request') == 'true'
    is_filtering = any(k in request.GET for k in ['busca', 'marca_id', 'condicao', 'localizacao', 'view'])

    if is_htmx and is_filtering:
        return render(request, 'carrinhos/partials/list.html', {
            'carrinhos': carrinhos,
            'view': view
        })

    marcas = Marca.objects.all().order_by('nome')
    localizacoes = (
        Carrinho.objects.exclude(localizacao__isnull=True)
        .exclude(localizacao__exact='')
        .values_list('localizacao', flat=True)
        .distinct()
        .order_by('localizacao')
    )

    return render(request, 'carrinhos/index.html', {
        'carrinhos': carrinhos,
        'marcas': marcas,
        'localizacoes': localizacoes,
        'busca': busca,
        'marca_id_selecionada': int(marca_id) if marca_id.isdigit() else 0,
        'condicao_selecionada': condicao,
        'localizacao_selecionada': localizacao,
        'view': view,
        'active_page': 'carrinhos',
    })

def form_novo_carrinho(request):
    marca_id_raw = request.GET.get('marca_id', '0')
    marca_id = int(marca_id_raw) if marca_id_raw.isdigit() else 0
    marcas = Marca.objects.all().order_by('nome')

    if marca_id > 0:
        modelos = Modelo.objects.filter(marca_id=marca_id).order_by('nome')
    else:
        modelos = Modelo.objects.select_related('marca').order_by('marca__nome', 'nome')

    return render(request, 'carrinhos/form.html', {
        'carrinho': None,
        'marcas': marcas,
        'modelos': modelos,
        'marca_selecionada_id': marca_id,
        'titulo': "Adicionar Novo Carrinho à Coleção",
        'active_page': 'carrinhos'
    })

def carrinho_detail_delete_view(request, id):
    if request.method == 'DELETE':
        carrinho = get_object_or_404(Carrinho, id=id)
        carrinho.delete()

        view = request.GET.get('view', 'cards')
        carrinhos = Carrinho.objects.select_related('modelo', 'modelo__marca').order_by('-id')

        response = render(request, 'carrinhos/partials/list.html', {
            'carrinhos': carrinhos,
            'view': view
        })
        trigger_data = json.dumps({
            "showToast": {"value": f"Carrinho #{id} excluído com sucesso!", "type": "danger"},
            "stockChanged": True
        })
        response['HX-Trigger'] = trigger_data
        return response

    carrinho = get_object_or_404(Carrinho.objects.select_related('modelo', 'modelo__marca'), id=id)
    return render(request, 'carrinhos/detail.html', {
        'carrinho': carrinho,
        'lucro': carrinho.lucro,
        'active_page': 'carrinhos'
    })

def carrinho_editar_view(request, id):
    carrinho = get_object_or_404(Carrinho.objects.select_related('modelo', 'modelo__marca'), id=id)
    
    if request.method == 'POST':
        modelo_id = request.POST.get('modelo_id')
        carrinho.modelo = get_object_or_404(Modelo, id=modelo_id)

        ano_raw = request.POST.get('ano_fabricacao', '').strip()
        carrinho.ano_fabricacao = int(ano_raw) if ano_raw.isdigit() else None

        carrinho.escala = request.POST.get('escala', '1:64').strip()
        carrinho.cor = request.POST.get('cor', '').strip()
        carrinho.serie_colecao = request.POST.get('serie_colecao', '').strip()
        carrinho.condicao = request.POST.get('condicao', 'Blister/Cartela Fechada').strip()
        carrinho.codigo_barra_sku = request.POST.get('codigo_barra_sku', '').strip()
        carrinho.localizacao = request.POST.get('localizacao', '').strip()
        
        qtd_raw = request.POST.get('quantidade', '1')
        try:
            carrinho.quantidade = max(0, int(qtd_raw))
        except ValueError:
            carrinho.quantidade = 1

        preco_raw = request.POST.get('preco_compra', '0.0').replace(',', '.')
        try:
            carrinho.preco_compra = float(preco_raw)
        except ValueError:
            carrinho.preco_compra = 0.0

        valor_raw = request.POST.get('valor_estimado', '0.0').replace(',', '.')
        try:
            carrinho.valor_estimado = float(valor_raw)
        except ValueError:
            carrinho.valor_estimado = 0.0

        carrinho.observacoes = request.POST.get('observacoes', '').strip()
        carrinho.save()

        return redirect(f"/carrinhos/{carrinho.id}?atualizado=true")

    marcas = Marca.objects.all().order_by('nome')
    modelos = Modelo.objects.filter(marca_id=carrinho.modelo.marca_id).order_by('nome')

    return render(request, 'carrinhos/form.html', {
        'carrinho': carrinho,
        'marcas': marcas,
        'modelos': modelos,
        'marca_selecionada_id': carrinho.modelo.marca_id,
        'titulo': f"Editar Carrinho #{carrinho.id}",
        'active_page': 'carrinhos'
    })
