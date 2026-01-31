from django.db import models
import uuid

# ============================================
# 1. MEMBRES
# ============================================
class Membres(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    code_MASSAR = models.CharField(max_length=20, unique=True)
    telephone = models.CharField(max_length=15, blank=True, null=True)
    filliere = models.CharField(max_length=100)
    login = models.CharField(max_length=50, unique=True)
    mot_de_passe = models.CharField(max_length=128)
    points = models.IntegerField(default=0)
    rang = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    uuid_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    class Meta:
        ordering = ['nom']
        verbose_name = "Membre"
        verbose_name_plural = "Membres"


# ============================================
# 2. ÉVÉNEMENT (Logistique)
# ============================================
class Evenement(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_debut = models.DateField()
    nombre_jours = models.IntegerField(default=1)
    lieu = models.CharField(max_length=200)
    points_par_jour = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    participants = models.ManyToManyField('Membres', related_name='evenements', blank=True)
    
    def __str__(self):
        return self.titre
    
    def get_jours_evenement(self):
        from datetime import timedelta
        return [self.date_debut + timedelta(days=i) for i in range(self.nombre_jours)]
    
    class Meta:
        ordering = ['-date_debut']
        verbose_name = "Événement"
        verbose_name_plural = "Événements"


# ============================================
# 3. TEMPLATE CERTIFICAT (Design)
# ============================================
class CertificateTemplate(models.Model):
    evenement = models.OneToOneField(
        Evenement, 
        on_delete=models.CASCADE, 
        related_name='template_certificat',
        verbose_name="Événement associé"
    )
    
    image_fond = models.ImageField(
        upload_to='certificats_templates/',
        verbose_name="Image de fond (A4 Paysage)"
    )
    
    # Coordonnées du NOM
    nom_x = models.IntegerField(default=420, verbose_name="Position X du Nom", help_text="Centre ~420")
    nom_y = models.IntegerField(default=300, verbose_name="Position Y du Nom", help_text="Bas=0, Haut=595")
    text_color = models.CharField(max_length=7, default="#000000", verbose_name="Couleur Texte (Hex)")
    
    # Police
    police_ttf = models.FileField(
        upload_to='fonts/', 
        blank=True, null=True, 
        verbose_name="Police personnalisée (.ttf)",
        help_text="Laissez vide pour Helvetica standard."
    )
    taille_police = models.IntegerField(default=45, verbose_name="Taille de la police")

    # Signature (Optionnel)
    signature = models.ImageField(
        upload_to='signatures/', 
        blank=True, null=True, 
        verbose_name="Signature (PNG Transparent)"
    )
    sign_x = models.IntegerField(default=600, verbose_name="Pos X Signature")
    sign_y = models.IntegerField(default=150, verbose_name="Pos Y Signature")

    def __str__(self):
        return f"Design Certificat - {self.evenement.titre}"

    class Meta:
        verbose_name = "Configuration du Certificat"
        verbose_name_plural = "Configurations des Certificats"


# ============================================
# 4. PRÉSENCE
# ============================================
class Presence(models.Model):
    STATUTS = [('present', 'Présent'), ('absent', 'Absent')]
    membre = models.ForeignKey(Membres, on_delete=models.CASCADE, related_name='presences')
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='presences')
    jour = models.DateField()
    date_scan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUTS, default='present')
    
    class Meta:
        unique_together = ('membre', 'evenement', 'jour')
        ordering = ['-date_scan']
        verbose_name = "Présence"
        verbose_name_plural = "Présences"


# ============================================
# 5. CERTIFICAT DÉLIVRÉ (Preuve)
# ============================================
class Certificate(models.Model):
    membre = models.ForeignKey(Membres, on_delete=models.CASCADE, related_name='certificates')
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='certificates_delivres')
    titre = models.CharField(max_length=200)
    date_obtention = models.DateTimeField(auto_now_add=True)
    code_verification = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"Certificat: {self.membre.nom} ({self.evenement.titre})"
    
    class Meta:
        unique_together = ('membre', 'evenement')
        ordering = ['-date_obtention']
        verbose_name = "Certificat Délivré"
        verbose_name_plural = "Certificats Délivrés"


# ============================================
# 6. AUTRES (Team, Annonce)
# ============================================
class TeamMember(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    poste = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='team/')
    bio = models.TextField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

class Annonce(models.Model):
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    auteur = models.ForeignKey(Membres, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)