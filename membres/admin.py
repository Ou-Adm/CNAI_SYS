from django.contrib import admin
from .models import *
from django.utils.html import format_html

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
    list_display = ('titre', 'date_debut', 'nombre_jours', 'lieu', 'points_par_jour', 'nombre_participants', 'actif')
    list_filter = ('actif', 'date_debut')
    list_editable = ('actif',)
    search_fields = ('titre', 'lieu')
    
    # On garde le champ 'participants' dans readonly pour qu'il ne soit pas modifiable
    readonly_fields = ('liste_des_presents',) 

    # On retire 'participants' d'ici pour ne plus voir les boîtes de sélection
    # filter_horizontal = ('participants',)  <-- On supprime ou commente cette ligne

    fieldsets = (
        ('Informations de base', {
            'fields': ('titre', 'description', 'lieu')
        }),
        ('Durée et points', {
            'fields': ('date_debut', 'nombre_jours', 'points_par_jour')
        }),
        ('Participants (Lecture Seule)', {
            # On affiche notre fonction personnalisée au lieu du champ standard
            'fields': ('liste_des_presents',) 
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )

    fieldsets = (
        ('Informations Générales', {
            'fields': ('titre', 'description', 'lieu', 'actif')
        }),
        ('Dates & Points', {
            'fields': ('date_debut', 'nombre_jours', 'points_par_jour')
        }),
        ('Personnalisation du Certificat', {
            'description': "Configurez l'apparence du PDF pour cet événement.",
            'fields': ('image_certificat', 'cert_nom_x', 'cert_nom_y', 'cert_text_color')
        }),
        ('Participants', {
            'fields': ('participants',) # Si tu utilises ManyToMany
        }),
    )

    def nombre_participants(self, obj):
        return obj.participants.count()
    nombre_participants.short_description = "Nb Participants"

    # --- NOUVELLE FONCTION POUR LISTER LES NOMS ---
    def liste_des_presents(self, obj):
        presents = obj.participants.all()
        
        if not presents:
            return "Aucun participant pour le moment."
            
        # On crée une liste HTML simple
        html_content = "<ul style='margin-left: 0; padding-left: 15px;'>"
        for p in presents:
            html_content += f"<li style='margin-bottom: 5px;'>👤 <strong>{p.prenom} {p.nom}</strong> ({p.filliere})</li>"
        html_content += "</ul>"
        
        return format_html(html_content)
    
    liste_des_presents.short_description = "Liste des Membres Scannés"


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
# admin.py

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('titre', 'membre', 'evenement', 'date_obtention')
    list_filter = ('evenement', 'date_obtention')
    search_fields = ('membre__nom', 'membre__prenom', 'titre')
    readonly_fields = ('date_obtention',)
    
    fieldsets = (
        ('Informations', {
            'fields': ('titre', 'membre', 'evenement', 'jours_assistes', 'date_obtention')
        }),
        ('Personnalisation du PDF', {
            'description': "Design du texte (Position, Couleur et Police).",
            # ✅ On ajoute 'police_ttf' ici
            'fields': ('cert_nom_x', 'cert_nom_y', 'cert_text_color', 'police_ttf')
        }),
    )


# ============================================
# ADMIN ANNONCE
# ============================================
@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('titre', 'contenu')
    readonly_fields = ('date_creation', 'date_modification')