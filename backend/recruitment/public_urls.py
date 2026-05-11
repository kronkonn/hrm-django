from django.urls import path
from . import public_views

urlpatterns = [
    path('vacancy/<uuid:token>/', public_views.public_vacancy_detail, name='public_vacancy_detail'),
    path('vacancy/<uuid:token>/apply/', public_views.public_vacancy_apply, name='public_vacancy_apply'),
]
