from django.db.models import Sum
from .models import Carrinho

def global_stock_counter(request):
    total = Carrinho.objects.aggregate(total=Sum('quantidade'))['total'] or 0
    return {
        'total_itens_estoque': total
    }
