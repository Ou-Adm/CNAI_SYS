from django.contrib import admin
from .models import *

# ============================================
# ADMIN MEMBRES
# ============================================
@admin.register(Membres)
class MembresAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'login', 'points', 'uuid_code')
    list_filter = ('date_inscription', 'filliere')
    search_fields = ('nom', 'prenom', 'email', 'login')
    readonly_fields = ('uuid_code', 'date_inscription')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('prenom', 'nom', 'email', 'telephone', 'photo')
        }),
        ('Scolaire', {
            'fields': ('code_MASSAR', 'filliere')
        }),
        ('Authentification', {
            'fields': ('login', 'mot_de_passe')
        }),
        ('Système', {
            'fields': ('points', 'rang', 'uuid_code', 'date_inscription')
        }),
    )


# ============================================
# ADMIN ÉQUIPE
# ============================================
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'poste', 'actif', 'ordre')
    list_editable = ('actif', 'ordre')
    list_filter = ('actif', 'date_creation')
    search_fields = ('nom', 'prenom', 'poste')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('prenom', 'nom', 'poste', 'bio')
        }),
        ('Photo et réseaux sociaux', {
            'fields': ('photo', 'instagram', 'linkedin', 'github', 'email')
        }),
        ('Affichage', {
            'fields': ('ordre', 'actif')
        }),
    )


# ============================================
# ADMIN ÉVÉNEMENT
# ============================================
@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_debut', 'nombre_jours', 'lieu', 'points_par_jour', 'actif')
    list_filter = ('actif', 'date_debut')
    list_editable = ('actif',)
    search_fields = ('titre', 'lieu')
    fieldsets = (
        ('Informations de base', {
            'fields': ('titre', 'description', 'lieu')
        }),
        ('Durée et points', {
            'fields': ('date_debut', 'nombre_jours', 'points_par_jour')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )


# ============================================
# ADMIN PRÉSENCE
# ============================================
@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('membre', 'evenement', 'jour', 'status', 'date_scan')
    list_filter = ('status', 'evenement', 'jour')
    search_fields = ('membre__nom', 'membre__prenom', 'evenement__titre')
    readonly_fields = ('date_scan',)


# ============================================
# ADMIN CERTIFICAT
# ============================================
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('titre', 'membre', 'evenement', 'jours_assistes', 'date_obtention')
    list_filter = ('evenement', 'date_obtention')
    search_fields = ('membre__nom', 'membre__prenom', 'titre')
    readonly_fields = ('date_obtention',)


# ============================================
# ADMIN ANNONCE
# ============================================
@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('titre', 'contenu')
    readonly_fields = ('date_creation', 'date_modification')