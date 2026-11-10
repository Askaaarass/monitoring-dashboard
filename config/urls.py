from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from apps.authentication.views import dashboard_view
from apps.sensors.views import BiomassIndexView, SensorViewSet, AlertViewSet, test_control_view
from apps.devices.views import DeviceViewSet
from apps.analytics.views import AuditLogViewSet, export_csv_view

admin.site.site_header = 'Аквапоника · управление системой'
admin.site.site_title = 'Администрирование аквапоники'
admin.site.index_title = 'Состояние и данные системы'

router = DefaultRouter()
router.register(r'sensors', SensorViewSet, basename='sensor')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='project.html'), name='project'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('test-control/', test_control_view, name='test_control'), # Новая страница тестов
    path('export-csv/', export_csv_view, name='export_csv'),
    path('auth/', include('apps.authentication.urls')),
    path('api/v1/biomass-index/', BiomassIndexView.as_view(), name='biomass_index'),
    path('api/v1/', include(router.urls)),
]