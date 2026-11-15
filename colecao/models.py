from django.db import models

class Marca(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    pais_origem = models.CharField(max_length=100, blank=True, null=True)
    ano_fundacao = models.IntegerField(blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    site_oficial = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'marcas'
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Modelo(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='modelos', db_column='marca_id')
    nome = models.CharField(max_length=200)
    tipo_carroceria = models.CharField(max_length=100, blank=True, null=True)
    ano_lancamento = models.IntegerField(blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'modelos'
        ordering = ['marca__nome', 'nome']

    def __str__(self):
        return f"{self.marca.nome} - {self.nome}"

    @property
    def marca_nome(self):
        return self.marca.nome

class Carrinho(models.Model):
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, related_name='carrinhos', db_column='modelo_id')
    ano_fabricacao = models.IntegerField(blank=True, null=True)
    escala = models.CharField(max_length=50, default='1:64', blank=True, null=True)
    cor = models.CharField(max_length=100)
    serie_colecao = models.CharField(max_length=150, blank=True, null=True)
    condicao = models.CharField(max_length=100, default='Blister/Cartela Fechada')
    codigo_barra_sku = models.CharField(max_length=100, blank=True, null=True)
    localizacao = models.CharField(max_length=150, blank=True, null=True)
    quantidade = models.IntegerField(default=1)
    preco_compra = models.FloatField(default=0.0)
    valor_estimado = models.FloatField(default=0.0)
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carrinhos'
        ordering = ['-id']

    def __str__(self):
        return f"{self.modelo.nome} ({self.cor})"

    @property
    def valor_total_item(self):
        if hasattr(self, '_valor_total_item'):
            return self._valor_total_item
        return (self.quantidade or 0) * (self.valor_estimado or 0.0)

    @valor_total_item.setter
    def valor_total_item(self, val):
        self._valor_total_item = val

    @property
    def lucro(self):
        return (self.valor_estimado or 0.0) - (self.preco_compra or 0.0)

    @property
    def modelo_nome(self):
        return self.modelo.nome

    @property
    def marca_nome(self):
        return self.modelo.marca.nome

    @property
    def marca_id(self):
        return self.modelo.marca_id

    @property
    def marca_pais(self):
        return self.modelo.marca.pais_origem

    @property
    def tipo_carroceria(self):
        return self.modelo.tipo_carroceria
