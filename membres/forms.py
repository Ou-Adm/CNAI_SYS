from django import forms
from .models import Membres

class MembreSettingsForm(forms.ModelForm):
    # Champ spécifique pour changer le mot de passe (non lié directement au modèle au début)
    nouveau_mot_de_passe = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'placeholder': 'Laisser vide pour ne pas changer'}),
        label="Nouveau mot de passe"
    )

    class Meta:
        model = Membres
        # Liste des champs que l'utilisateur a le droit de modifier
        fields = ['prenom', 'nom', 'email', 'telephone', 'photo']
        
        widgets = {
            'prenom': forms.TextInput(attrs={'placeholder': 'Votre prénom'}),
            'nom': forms.TextInput(attrs={'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}), # Souvent on empêche de changer l'email
            'telephone': forms.TextInput(attrs={'placeholder': '06XXXXXXXX'}),
        }

    def clean_email(self):
        # Empêcher la modification de l'email si tu le souhaites, sinon retire cette méthode
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.email
        return self.cleaned_data['email']