from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # 1. La racine '' pointe maintenant vers l'INTRO 3D
    path('', views.landing, name='landing'),

    # 2. La page principale (vidéo/dashboard) devient accessible via '/home/'
    path('home/', views.index, name='index'),

    # ... le reste de vos URLs (login, etc.) ne change pas ...
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('my-qr/', views.member_qr_code, name='my_qr'),
    path('certificate/', views.certificate, name='certificate'),
    path('certificate/download/<int:certificate_id>/', views.generate_certificate_pdf, name='download_certificate'),
    path('team/', views.team, name='team'),
    path('events/', views.events, name='events'),
    path('calendar/', views.calendar, name='calendar'),
    path('announcements/', views.announcements, name='announcements'),
    path('ranking/', views.ranking, name='ranking'),
    path('send-application/', views.send_application, name='send_application'),
    path('scan/', views.scan_page, name='scan'),
    path('api/scan-qr/', views.scan_qr_code, name='scan_qr_code'),
    path('api/stats/<int:evenement_id>/', views.attendance_stats, name='attendance_stats'),
    path('contact/', views.contact, name='contact'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)