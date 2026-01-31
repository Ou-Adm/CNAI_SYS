from django.contrib import admin
from .models import *
from django.utils.html import format_html

# ============================================
# 1. MEMBRES
# ============================================
@admin.register(Membres)
class MembresAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'points')
    search_fields = ('nom', 'prenom', 'email')

# ============================================
# 2. ÉVÉNEMENTS
# ============================================
@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_debut', 'nombre_jours', 'has_template', 'actif')
    list_filter = ('actif', 'date_debut')
    readonly_fields = ('liste_des_presents',)
    
    fieldsets = (
        ('Infos Générales', {'fields': ('titre', 'description', 'lieu', 'actif')}),
        ('Dates & Points', {'fields': ('date_debut', 'nombre_jours', 'points_par_jour')}),
        ('Participants', {'fields': ('liste_des_presents',)}),
    )

    def liste_des_presents(self, obj):
        presents = obj.participants.all()
        if not presents: return "Aucun participant."
        html = "<ul style='margin-left:0;padding-left:15px;'>"
        for p in presents:
            html += f"<li>👤 {p.prenom} {p.nom}</li>"
        return format_html(html + "</ul>")
    
    def has_template(self, obj):
        return hasattr(obj, 'template_certificat')
    has_template.boolean = True
    has_template.short_description = "Template Configuré ?"

# ============================================
# 3. CONFIGURATION CERTIFICATS (Template)
# ============================================
@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('evenement', 'preview_image', 'taille_police')
    search_fields = ('evenement__titre',)
    
    fieldsets = (
        ('Liaison Événement', {
            'fields': ('evenement',)
        }),
        ('Visuel', {
            'fields': ('image_fond', 'police_ttf', 'text_color', 'taille_police')
        }),
        ('Position Nom', {
            'fields': ('nom_x', 'nom_y')
        }),
        ('Signature (Optionnel)', {
            'fields': ('signature', 'sign_x', 'sign_y')
        }),
    )

    def preview_image(self, obj):
        if obj.image_fond:
            return format_html('<img src="{}" style="width: 100px; height: auto;" />', obj.image_fond.url)
        return "-"
    preview_image.short_description = "Aperçu"

# ============================================
# 4. CERTIFICATS DÉLIVRÉS (Preuves)
# ============================================
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('membre', 'evenement', 'date_obtention')
    list_filter = ('evenement', 'date_obtention')
    search_fields = ('membre__nom', 'titre')
    readonly_fields = ('date_obtention', 'code_verification')
    
    fieldsets = (
        ('Détails', {
            'fields': ('titre', 'membre', 'evenement', 'date_obtention')
        }),
    )
    
    def has_add_permission(self, request):
        return False

# ============================================
# 5. AUTRES
# ============================================
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'poste', 'actif', 'ordre')
    list_editable = ('ordre', 'actif')