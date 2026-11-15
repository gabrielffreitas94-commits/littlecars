from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/estoque', permanent=False)),
    path('', include('colecao.urls')),
]
