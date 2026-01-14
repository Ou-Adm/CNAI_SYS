from django.urls import path
from . import views

urlpatterns = [
    # --- CORRECTION ICI ---
    # 1. La racine '' DOIT pointer vers 'landing' (L'intro 3D)
    path('', views.landing, name='landing'),

    # 2. On déplace l'ancienne page d'accueil vers 'home/'
    path('home/', views.index, name='index'),
    # ----------------------

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('team/', views.team, name='team'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('announcements/', views.announcements, name='announcements'),
    path('calendar/', views.calendar, name='calendar'),
    path('ranking/', views.ranking, name='ranking'),
    path('certificate/', views.certificate, name='certificate'),
    path('settings/', views.settings, name='settings'),   
    path('events/', views.events, name='events'),
    path('my-qr/', views.member_qr_code, name='my_qr'),
    path('scan/', views.scan_page, name='scan'),
    path('api/scan-qr/', views.scan_qr_code, name='scan_qr_code'),
    path('api/stats/<int:evenement_id>/', views.attendance_stats, name='attendance_stats'),
    path('certificate/download/<int:certificate_id>/', views.generate_certificate_pdf, name='download_certificate'),
    path('send-application/', views.send_application, name='send_application'),
]