from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail

from datetime import date, timedelta
import json
import qrcode
import base64
import calendar as cal_lib
import io  
from io import BytesIO 

# ReportLab imports pour PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Imports locaux
from .models import Membres, TeamMember, Annonce, Certificate, Evenement, Presence
from .forms import MembreSettingsForm

# ============================================
# 1️⃣ AUTHENTIFICATION & UTILITAIRES
# ============================================

def get_is_member(request):
    """Retourne True si l'utilisateur est connecté (admin ou membre)"""
    return request.user.is_authenticated or 'membre_id' in request.session

def require_login(request):
    """Autorise superuser Django OU membre interne"""
    if request.user.is_authenticated:
        return True
    if 'membre_id' in request.session:
        return True
    return False

def index(request):
    context = {'is_member': 'membre_id' in request.session}
    return render(request, 'membres/index.html', context)

def login_view(request):
    """Connexion superuser OU membre normal"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 1) Tentative d'auth Django (Admin / Staff)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            django_login(request, user)
            return redirect('index')

        # 2) Tentative d'auth membre personnalisé
        try:
            membre = Membres.objects.get(login=username)
            # Note: Pour une vraie sécurité, utilise pbkdf2_sha256 au lieu du texte clair
            if membre.mot_de_passe == password:
                request.session['membre_id'] = membre.id
                return redirect('index')
            else:
                return render(request, 'membres/login.html', {'error': 'Mot de passe incorrect.'})
        except Membres.DoesNotExist:
            return render(request, 'membres/login.html', {'error': 'Utilisateur introuvable.'})

    return render(request, 'membres/login.html')

def logout_view(request):
    """Déconnexion hybride"""
    if request.user.is_authenticated:
        django_logout(request)
    request.session.flush()
    return redirect('login')

# ============================================
# 2️⃣ ESPACE MEMBRE (Vues protégées)
# ============================================

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

def settings(request):
    if not require_login(request):
        return redirect('login')

    # Si c'est un admin Django, pas de settings membre pour l'instant
    if request.user.is_authenticated:
        return render(request, 'membres/settings.html', {'is_admin': True})
    
    membre = Membres.objects.get(id=request.session['membre_id'])

    if request.method == 'POST':
        form = MembreSettingsForm(request.POST, request.FILES, instance=membre)
        if form.is_valid():
            nouveau_mdp = form.cleaned_data.get('nouveau_mot_de_passe')
            if nouveau_mdp:
                membre.mot_de_passe = nouveau_mdp
            form.save()
            messages.success(request, "✅ Vos informations ont été mises à jour avec succès !")
            return redirect('settings')
        else:
            messages.error(request, "❌ Erreur lors de la mise à jour.")
    else:
        form = MembreSettingsForm(instance=membre)

    return render(request, 'membres/settings.html', {
        'form': form,
        'membre': membre,
        'is_member': get_is_member(request)
    })

def member_qr_code(request):
    """Affiche le QR code du membre connecté"""
    if not require_login(request):
        return redirect('login')
    
    if request.user.is_authenticated:
        return redirect('index')  # Admin n'a pas de QR code membre
    
    membre = Membres.objects.get(id=request.session['membre_id'])
    
    # Génération du QR Code à la volée
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(membre.uuid_code))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    qr_code_img = f"data:image/png;base64,{img_str}"
    
    return render(request, 'membres/my_qr.html', {
        'membre': membre,
        'qr_code': qr_code_img,
        'is_member': get_is_member(request)
    })

def certificate(request):
    if not require_login(request):
        return redirect('login')

    # Seuls les membres ont des certificats (pas les admins)
    if request.user.is_authenticated:
         return redirect('index')

    membre = Membres.objects.get(id=request.session['membre_id'])
    certificates = Certificate.objects.filter(membre=membre)

    return render(request, 'membres/certificate.html', {
        'certificates': certificates,
        'is_member': get_is_member(request)
    })

def ranking(request):
    if not require_login(request):
        return redirect('login')

    membre_id = request.session.get('membre_id')
    
    # On récupère tout le monde trié par points décroissants
    all_members_qs = Membres.objects.all().order_by('-points')
    
    # Calcul du rang
    rank = '-'
    if membre_id:
        all_ids = list(all_members_qs.values_list('id', flat=True))
        if membre_id in all_ids:
            rank = all_ids.index(membre_id) + 1

    # Découpage pour l'affichage (Top 3 et Top 10)
    top3 = all_members_qs[:3]
    rest_of_top10 = all_members_qs[3:13]

    # Pour l'affichage, on récupère l'objet membre si connecté
    membre = Membres.objects.get(id=membre_id) if membre_id else None

    return render(request, 'membres/ranking.html', {
        'membre': membre,
        'my_rank': rank,
        'top3': top3,
        'rest_of_list': rest_of_top10,
        'is_member': get_is_member(request)
    })

# ============================================
# 3️⃣ PUBLIC / COMMUNAUTÉ
# ============================================

def team(request):
    members = TeamMember.objects.filter(actif=True)
    return render(request, 'membres/team.html', {
        'members': members,
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

def events(request):
    return calendar(request) # Redirige vers la vue calendrier complète

def calendar(request):
    # 1. Gestion de la date
    today = timezone.now().date()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year = today.year
        month = today.month

    # 2. Noms des mois
    MOIS_FR = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }

    # 3. Récupérer les événements actifs
    all_events = Evenement.objects.filter(actif=True)

    # 4. Configurer le calendrier (Commence le Dimanche = 6)
    cal = cal_lib.Calendar(firstweekday=6)
    month_days = []
    
    # 5. Construire la grille
    for week in cal.monthdatescalendar(year, month):
        for day in week:
            events_on_day = []
            
            for event in all_events:
                event_end_date = event.date_debut + timedelta(days=event.nombre_jours - 1)
                
                if event.date_debut <= day <= event_end_date:
                    colors = ['bg-blue', 'bg-purple', 'bg-green']
                    css_class = colors[event.id % 3] 
                    
                    events_on_day.append({
                        'title': event.titre,
                        'css_class': css_class,
                        'id': event.id
                    })

            month_days.append({
                'day_obj': day,
                'day_number': day.day,
                'is_current_month': (day.month == month),
                'events': events_on_day,
                'is_today': (day == today)
            })

    # 6. Navigation
    first_day_curr = date(year, month, 1)
    prev_month_date = first_day_curr - timedelta(days=1)
    next_month_date = (first_day_curr + timedelta(days=32)).replace(day=1)

    context = {
        'current_year': year,
        'current_month_name': MOIS_FR[month],
        'days': month_days,
        'prev_year': prev_month_date.year,
        'prev_month': prev_month_date.month,
        'next_year': next_month_date.year,
        'next_month': next_month_date.month,
        'is_member': get_is_member(request)
    }

    return render(request, 'membres/calendar.html', context)

def send_application(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        message_content = request.POST.get('message')

        subject = f"Nouvelle Candidature CNAI : {name}"
        body = f"""
        NOUVELLE DEMANDE D'ADHÉSION
        Nom: {name}
        Email: {email}
        Tel: {telephone}
        Message: {message_content}
        """

        try:
            # Pense à configurer EMAIL_HOST_USER dans settings.py
            send_mail(subject, body, 'noreply@tonasso.com', ['admin@tonasso.com'], fail_silently=False)
            messages.success(request, "Candidature transmise avec succès !")
        except Exception as e:
            messages.error(request, "Erreur de transmission.")
            print(f"Mail error: {e}")

        return redirect('index')
    return redirect('index')

# ============================================
# 4️⃣ ADMIN / STAFF (SCAN & GESTION)
# ============================================

def scan_page(request):
    """Page pour scanner les QR codes (Seulement Admin/Staff)"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    evenements = Evenement.objects.filter(actif=True).order_by('-date_debut')
    
    return render(request, 'membres/scan.html', {
        'evenements': evenements,
        'is_member': get_is_member(request)
    })

@csrf_exempt
@require_http_methods(["POST"])
def scan_qr_code(request):
    """
    API pour scanner un QR Code.
    Ajoute le membre à l'événement et gère la présence.
    """
    # 🔒 SÉCURITÉ : Seul un admin connecté peut valider un scan
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': '⛔ Accès non autorisé (Admin requis)'}, status=403)

    try:
        data = json.loads(request.body)
        uuid_code = data.get('uuid_code')
        evenement_id = data.get('evenement_id')
        
        try:
            membre = Membres.objects.get(uuid_code=uuid_code)
        except Membres.DoesNotExist:
            return JsonResponse({'success': False, 'message': '❌ Membre inconnu'}, status=404)
        
        try:
            evenement = Evenement.objects.get(id=evenement_id, actif=True)
        except Evenement.DoesNotExist:
            return JsonResponse({'success': False, 'message': '❌ Événement introuvable'}, status=404)
        
        jour_actuel = date.today()
        jours_evenement = evenement.get_jours_evenement()
        
        if jour_actuel not in jours_evenement:
            return JsonResponse({'success': False, 'message': '❌ Cet événement ne se déroule pas aujourd\'hui'}, status=400)
        
        # Ajout global
        evenement.participants.add(membre)

        # Vérification doublon journalier
        if Presence.objects.filter(membre=membre, evenement=evenement, jour=jour_actuel).exists():
            return JsonResponse({'success': False, 'message': f'⚠️ {membre.prenom} a déjà été scanné aujourd\'hui'}, status=400)
        
        # Création présence
        Presence.objects.create(membre=membre, evenement=evenement, jour=jour_actuel, status='present')
        
        # Points
        membre.points += evenement.points_par_jour
        membre.save()
        
        # Check Certificat
        jours_assistes = Presence.objects.filter(membre=membre, evenement=evenement, status='present').count()
        nouveau_certificat = False
        
        if jours_assistes == evenement.nombre_jours:
            _, created = Certificate.objects.get_or_create(
                membre=membre,
                evenement=evenement,
                defaults={
                    'titre': f'Certificat - {evenement.titre}',
                    'jours_assistes': jours_assistes
                }
            )
            nouveau_certificat = created
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Bienvenue {membre.prenom}!',
            'data': {
                'nom': f"{membre.prenom} {membre.nom}",
                'points_total': membre.points,
                'jours_assistes': jours_assistes,
                'nouveau_certificat': nouveau_certificat
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Format invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def attendance_stats(request, evenement_id):
    """Voir les statistiques de présence d'un événement"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        evenement = Evenement.objects.get(id=evenement_id)
        presences = Presence.objects.filter(evenement=evenement)
        
        total_presents = presences.filter(status='present').count()
        certificats = Certificate.objects.filter(evenement=evenement).count()
        
        return JsonResponse({
            'titre': evenement.titre,
            'scans_total': total_presents,
            'certificats_generes': certificats,
        })
    except Evenement.DoesNotExist:
        return JsonResponse({'error': 'Événement non trouvé'}, status=404)

def generate_certificate_pdf(request, certificate_id):
    """Génération du PDF du certificat"""
    cert = get_object_or_404(Certificate, id=certificate_id)
    evt = cert.evenement

    # Sécurité : Un membre ne peut télécharger que SON certificat
    if 'membre_id' in request.session:
        if request.session['membre_id'] != cert.membre.id:
            return redirect('index')
    elif not request.user.is_authenticated:
        return redirect('login')

    buffer = io.BytesIO()
    # Orientation Paysage
    width, height = landscape(A4)
    p = canvas.Canvas(buffer, pagesize=landscape(A4))

    # 1. DESSIN DU FOND
    if evt.image_certificat:
        try:
            p.drawImage(evt.image_certificat.path, 0, 0, width=width, height=height)
        except Exception:
            # Fallback fond blanc
            p.setFillColor(HexColor('#FFFFFF'))
            p.rect(0, 0, width, height, fill=1)
    else:
        p.setFillColor(HexColor('#FFFFFF'))
        p.rect(0, 0, width, height, fill=1)

    # 2. GESTION DE LA POLICE (FONT)
    font_name = "Helvetica-Bold"
    if cert.police_ttf:
        try:
            custom_font_name = f"CustomFont_{cert.id}"
            pdfmetrics.registerFont(TTFont(custom_font_name, cert.police_ttf.path))
            font_name = custom_font_name
        except Exception as e:
            print(f"Erreur police: {e}")

    # 3. ÉCRITURE DU NOM
    p.setFont(font_name, 45)
    try:
        text_color = HexColor(cert.cert_text_color)
    except:
        text_color = HexColor('#000000')
        
    p.setFillColor(text_color)
    
    nom_complet = f"{cert.membre.prenom} {cert.membre.nom}"
    
    # Utilisation des coordonnées stockées
    p.drawCentredString(cert.cert_nom_x, cert.cert_nom_y, nom_complet)

    p.showPage()
    p.save()
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f"Certificat_{cert.membre.nom}.pdf")


def landing(request):
    return render(request, 'membres/landing.html')