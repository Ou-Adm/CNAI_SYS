from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
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
    # 🎯 NOUVELLES URLs - QR CODE
    path('my-qr/', views.member_qr_code, name='my_qr'),  # ← AJOUTER CETTE LIGNE
    path('scan/', views.scan_page, name='scan'),
    path('api/scan-qr/', views.scan_qr_code, name='scan_qr_code'),
    path('api/stats/<int:evenement_id>/', views.attendance_stats, name='attendance_stats'),
]
