from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from .models import Membres, TeamMember, Annonce, Certificate, Evenement, Presence
import json
import qrcode
from io import BytesIO
import base64


def index(request):
    context = {'is_member': 'membre_id' in request.session}
    return render(request, 'membres/index.html', context)


def login_view(request):
    """Connexion superuser OU membre normal"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # === 1) Tentative d'auth Django (superuser/admin) ===
        user = authenticate(request, username=username, password=password)
        if user is not None:
            django_login(request, user)
            return redirect('index')

        # === 2) Tentative d'auth membre personnalisé ===
        try:
            membre = Membres.objects.get(login=username)

            if membre.mot_de_passe == password:
                request.session['membre_id'] = membre.id
                return redirect('index')
            else:
                return render(request, 'membres/login.html', {
                    'error': 'Mot de passe incorrect.'
                })

        except Membres.DoesNotExist:
            return render(request, 'membres/login.html', {
                'error': 'Utilisateur introuvable.'
            })

    return render(request, 'membres/login.html')


def logout_view(request):
    """Déconnexion hybride"""
    if request.user.is_authenticated:
        django_logout(request)

    request.session.flush()
    return redirect('login')


# ========= UTILITAIRE COMMUN POUR PROTÉGER LES VUES ========= #

def require_login(request):
    """Autorise superuser Django OU membre interne"""
    if request.user.is_authenticated:
        return True

    if 'membre_id' in request.session:
        return True

    return False


def get_is_member(request):
    """Retourne True si l'utilisateur est connecté (admin ou membre)"""
    return request.user.is_authenticated or 'membre_id' in request.session


def dashboard(request):
    if not require_login(request):
        return redirect('login')

    membre = None
    user = None

    if request.user.is_authenticated:
        user = request.user
    else:
        membre = Membres.objects.get(id=request.session['membre_id'])

    return render(request, 'membres/dashboard.html', {
        'membre': membre,
        'user': user,
        'is_member': get_is_member(request)
    })


def team(request):
    members = TeamMember.objects.filter(actif=True)
    return render(request, 'membres/team.html', {
        'members': members,
        'is_member': get_is_member(request)
    })


def profile(request):
    if not require_login(request):
        return redirect('login')

    if request.user.is_authenticated:
        return render(request, 'membres/profile.html', {
            'user': request.user,
            'is_member': get_is_member(request)
        })

    membre = Membres.objects.get(id=request.session['membre_id'])
    return render(request, 'membres/profile.html', {
        'membre': membre,
        'is_member': get_is_member(request)
    })


def announcements(request):
    if not require_login(request):
        return redirect('login')

    annonces = Annonce.objects.all()
    return render(request, 'membres/announcements.html', {
        'annonces': annonces,
        'is_member': get_is_member(request)
    })


def calendar(request):
    if not require_login(request):
        return redirect('login')

    return render(request, 'membres/calendar.html', {
        'is_member': get_is_member(request)
    })


def ranking(request):
    if not require_login(request):
        return redirect('login')

    membre = Membres.objects.get(id=request.session['membre_id'])
    all_members = Membres.objects.all().order_by('-points')
    rank = list(all_members.values_list('id', flat=True)).index(membre.id) + 1

    return render(request, 'membres/ranking.html', {
        'membre': membre,
        'all_members': all_members,
        'rank': rank,
        'is_member': get_is_member(request)
    })


def certificate(request):
    if not require_login(request):
        return redirect('login')

    membre = Membres.objects.get(id=request.session['membre_id'])
    certificates = Certificate.objects.filter(membre=membre)

    return render(request, 'membres/certificate.html', {
        'certificates': certificates,
        'is_member': get_is_member(request)
    })


def settings(request):
    if not require_login(request):
        return redirect('login')

    return render(request, 'membres/settings.html', {
        'is_member': get_is_member(request)
    })


# ============================================
# 🎯 QR CODE
# ============================================

def get_qr_code_image(uuid_code):
    """Génère un QR code en base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(uuid_code))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def member_qr_code(request):
    """Affiche le QR code du membre connecté"""
    if not require_login(request):
        return redirect('login')
    
    if request.user.is_authenticated:
        return redirect('index')  # Admin n'a pas de QR code
    
    membre = Membres.objects.get(id=request.session['membre_id'])
    qr_code = get_qr_code_image(membre.uuid_code)
    
    return render(request, 'membres/my_qr.html', {
        'membre': membre,
        'qr_code': qr_code,
        'is_member': get_is_member(request)
    })


def scan_page(request):
    """Page pour scanner les QR codes"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    evenements = Evenement.objects.filter(actif=True).order_by('-date_debut')
    
    return render(request, 'membres/scan.html', {
        'evenements': evenements,
        'is_member': get_is_member(request)
    })


# ============================================
# 🎯 SCAN QR CODE API
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def scan_qr_code(request):
    """
    Endpoint pour scanner un QR Code lors d'un événement multi-jours
    
    JSON reçu:
    {
        "uuid_code": "a1b2c3d4-...",
        "evenement_id": 1
    }
    """
    try:
        data = json.loads(request.body)
        uuid_code = data.get('uuid_code')
        evenement_id = data.get('evenement_id')
        
        # ✅ Vérifier que le membre existe
        try:
            membre = Membres.objects.get(uuid_code=uuid_code)
        except Membres.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '❌ Membre non reconnu'
            }, status=404)
        
        # ✅ Vérifier que l'événement existe
        try:
            evenement = Evenement.objects.get(id=evenement_id, actif=True)
        except Evenement.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '❌ Événement non trouvé ou terminé'
            }, status=404)
        
        # ✅ Obtenir le jour actuel
        jour_actuel = date.today()
        
        # ✅ Vérifier que le jour actuel fait partie de l'événement
        jours_evenement = evenement.get_jours_evenement()
        if jour_actuel not in jours_evenement:
            return JsonResponse({
                'success': False,
                'message': f'❌ Cet événement ne se déroule pas aujourd\'hui'
            }, status=400)
        
        # ✅ Vérifier si le membre a déjà scanné pour ce jour
        presence_today = Presence.objects.filter(
            membre=membre,
            evenement=evenement,
            jour=jour_actuel
        ).exists()
        
        if presence_today:
            return JsonResponse({
                'success': False,
                'message': f'⚠️ {membre.prenom} a déjà été scanné pour aujourd\'hui'
            }, status=400)
        
        # ✅ Créer l'enregistrement de présence pour ce jour
        presence = Presence.objects.create(
            membre=membre,
            evenement=evenement,
            jour=jour_actuel,
            status='present'
        )
        
        # ✅ Ajouter les points au membre
        membre.points += evenement.points_par_jour
        membre.save()
        
        # ✅ Compter combien de jours le membre a assisté
        jours_assistes = Presence.objects.filter(
            membre=membre,
            evenement=evenement,
            status='present'
        ).count()
        
        # ✅ Vérifier si le certificat doit être généré
        certificat_genere = False
        nouveau_certificat = False
        
        if jours_assistes == evenement.nombre_jours:
            # Le membre a assisté à TOUS les jours !
            certificat, created = Certificate.objects.get_or_create(
                membre=membre,
                evenement=evenement,
                defaults={
                    'titre': f'Certificat de participation - {evenement.titre}',
                    'jours_assistes': jours_assistes
                }
            )
            certificat_genere = True
            nouveau_certificat = created
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Bienvenue {membre.prenom} {membre.nom}!',
            'data': {
                'nom': membre.prenom + ' ' + membre.nom,
                'points_gaines': evenement.points_par_jour,
                'points_total': membre.points,
                'jour_actuel': jour_actuel.strftime('%d/%m/%Y'),
                'jours_assistes': jours_assistes,
                'jours_requis': evenement.nombre_jours,
                'certificat_genere': certificat_genere,
                'nouveau_certificat': nouveau_certificat,
                'message_certificat': f'🎓 Certificat généré! {jours_assistes}/{evenement.nombre_jours} jours' if nouveau_certificat else ''
            }
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '❌ Format JSON invalide'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Erreur serveur: {str(e)}'
        }, status=500)


def attendance_stats(request, evenement_id):
    """Voir les statistiques de présence d'un événement"""
    try:
        evenement = Evenement.objects.get(id=evenement_id)
        presences = Presence.objects.filter(evenement=evenement)
        
        total_presents = presences.filter(status='present').count()
        certificats = Certificate.objects.filter(evenement=evenement).count()
        
        return JsonResponse({
            'titre': evenement.titre,
            'nombre_jours': evenement.nombre_jours,
            'date_debut': evenement.date_debut.strftime('%d/%m/%Y'),
            'date_fin': evenement.get_date_fin().strftime('%d/%m/%Y'),
            'scans_total': total_presents,
            'certificats_generes': certificats,
        }, status=200)
    except Evenement.DoesNotExist:
        return JsonResponse({'error': 'Événement non trouvé'}, status=404)