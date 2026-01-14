from django.db import models
import uuid

# ============================================
# 1️⃣ MODÈLE MEMBRE
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
    
    # 🔑 UUID UNIQUE pour QR Code
    uuid_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    class Meta:
        ordering = ['nom']


# ============================================
# 2️⃣ MODÈLE ÉVÉNEMENT (MULTI-JOURS)
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
    image_certificat = models.ImageField(
        upload_to='certificats_templates/',
        blank=True, null=True, 
        verbose_name="Image de fond (Template)"
    )
    
    # Coordonnées pour le NOM DU MEMBRE
    cert_nom_x = models.IntegerField(
        default=420, 
        verbose_name="Position X du Nom (Gauche <-> Droite)",
        help_text="Centre de la page A4 = 420 environ"
    )
    cert_nom_y = models.IntegerField(
        default=300, 
        verbose_name="Position Y du Nom (Bas <-> Haut)",
        help_text="0 = Tout en bas. 595 = Tout en haut."
    )
    
    # Couleur du texte
    cert_text_color = models.CharField(
        max_length=7, 
        default="#000000", 
        verbose_name="Couleur du texte (Hex)",
        help_text="Ex: #000000 pour noir, #FFFFFF pour blanc, #FFD700 pour or"
    )

    # ✅ LISTE DES PARTICIPANTS (Relation Many-to-Many avec Membres)
    participants = models.ManyToManyField('Membres', related_name='evenements', blank=True)
    
    def __str__(self):
        return f"{self.titre} ({self.nombre_jours} jours)"
    
    def get_jours_evenement(self):
        """Retourne la liste de tous les jours"""
        from datetime import timedelta
        jours = []
        for i in range(self.nombre_jours):
            jour = self.date_debut + timedelta(days=i)
            jours.append(jour)
        return jours
    
    def get_date_fin(self):
        """Retourne la date de fin"""
        from datetime import timedelta
        return self.date_debut + timedelta(days=self.nombre_jours - 1)
    
    class Meta:
        ordering = ['-date_debut']


# ============================================
# 3️⃣ MODÈLE PRÉSENCE (PAR JOUR)
# ============================================
class Presence(models.Model):
    STATUTS = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
    ]
    
    membre = models.ForeignKey(Membres, on_delete=models.CASCADE, related_name='presences')
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='presences')
    jour = models.DateField()  # Jour spécifique
    date_scan = models.DateTimeField(auto_now_add=True)  # Timestamp du scan
    status = models.CharField(max_length=20, choices=STATUTS, default='present')
    
    def __str__(self):
        return f"{self.membre.prenom} - {self.evenement.titre} ({self.jour})"
    
    class Meta:
        unique_together = ('membre', 'evenement', 'jour')
        ordering = ['-date_scan']


# ============================================
# 4️⃣ MODÈLE CERTIFICAT
# ============================================
class Certificate(models.Model):
    membre = models.ForeignKey(Membres, on_delete=models.CASCADE, related_name='certificates')
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='certificates')
    titre = models.CharField(max_length=200)
    jours_assistes = models.IntegerField()
    date_obtention = models.DateTimeField(auto_now_add=True)
    
    # ✅ NOUVEAUX CHAMPS : Pour régler la position SUR CE CERTIFICAT PRÉCIS
    cert_nom_x = models.IntegerField(default=420, verbose_name="Position X (Gauche/Droite)")
    cert_nom_y = models.IntegerField(default=300, verbose_name="Position Y (Bas/Haut)")
    cert_text_color = models.CharField(max_length=7, default="#000000", verbose_name="Couleur Texte (Hex)")
    police_ttf = models.FileField(
        upload_to='fonts/', 
        blank=True, 
        null=True, 
        verbose_name="Fichier Police (.ttf)",
        help_text="Laissez vide pour utiliser Helvetica par défaut."
    )
    
    # ❌ ON A SUPPRIMÉ LE CHAMP 'fichier' CAR ON GÉNÈRE LE PDF AUTOMATIQUEMENT

    def __str__(self):
        return f"{self.titre} - {self.membre.prenom}"
    
    class Meta:
        unique_together = ('membre', 'evenement')
        ordering = ['-date_obtention']


# ============================================
# 5️⃣ MODÈLE ÉQUIPE
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
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    class Meta:
        ordering = ['ordre']


# ============================================
# 6️⃣ MODÈLE ANNONCE
# ============================================
class Annonce(models.Model):
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    auteur = models.ForeignKey(Membres, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_creation']


        