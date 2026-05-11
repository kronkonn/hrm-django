from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .search_views import GlobalSearchView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/employees/', include('employees.urls')),
    path('api/timesheets/', include('timesheets.urls')),
    path('api/leaves/', include('leaves.urls')),
    path('api/recruitment/', include('recruitment.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/training/', include('training.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/public/', include('recruitment.public_urls')),
    path('api/search/', GlobalSearchView.as_view(), name='global_search'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
