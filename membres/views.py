from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist

from datetime import date, timedelta
import json
import qrcode
import base64
import calendar as cal_lib
import io 

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
# 1. AUTHENTIFICATION & UTILITAIRES
# ============================================

def get_is_member(request):
    """Retourne True si l'utilisateur est connecté (admin ou membre)"""
    return request.user.is_authenticated or 'membre_id' in request.session

def require_login(request):
    if request.user.is_authenticated or 'membre_id' in request.session:
        return True
    return False

def index(request):
    upcoming_events = Evenement.objects.filter(
        date_debut__gte=date.today(), 
        actif=True
    ).order_by('date_debut')[:3]

    context = {
        'is_member': 'membre_id' in request.session,
        'upcoming_events': upcoming_events  
    }
    return render(request, 'membres/index.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Admin Django
        user = authenticate(request, username=username, password=password)
        if user is not None:
            django_login(request, user)
            return redirect('index')

        # Membre
        try:
            membre = Membres.objects.get(login=username)
            if membre.mot_de_passe == password:
                request.session['membre_id'] = membre.id
                return redirect('index')
            else:
                return render(request, 'membres/login.html', {'error': 'Mot de passe incorrect.'})
        except Membres.DoesNotExist:
            return render(request, 'membres/login.html', {'error': 'Utilisateur introuvable.'})

    return render(request, 'membres/login.html')

def logout_view(request):
    if request.user.is_authenticated:
        django_logout(request)
    request.session.flush()
    return redirect('login')

# ============================================
# 2. ESPACE MEMBRE
# ============================================

def dashboard(request):
    if not require_login(request): return redirect('login')

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
    if not require_login(request): return redirect('login')

    if request.user.is_authenticated:
        return render(request, 'membres/profile.html', {
            'user': request.user, 'is_member': get_is_member(request)
        })

    membre = Membres.objects.get(id=request.session['membre_id'])
    return render(request, 'membres/profile.html', {
        'membre': membre, 'is_member': get_is_member(request)
    })

def settings(request):
    if not require_login(request): return redirect('login')
    if request.user.is_authenticated:
        return render(request, 'membres/settings.html', {'is_admin': True})
    
    membre = Membres.objects.get(id=request.session['membre_id'])

    if request.method == 'POST':
        form = MembreSettingsForm(request.POST, request.FILES, instance=membre)
        if form.is_valid():
            nouveau_mdp = form.cleaned_data.get('nouveau_mot_de_passe')
            if nouveau_mdp: membre.mot_de_passe = nouveau_mdp
            form.save()
            messages.success(request, "✅ Informations mises à jour !")
            return redirect('settings')
        else:
            messages.error(request, "❌ Erreur mise à jour.")
    else:
        form = MembreSettingsForm(instance=membre)

    return render(request, 'membres/settings.html', {
        'form': form, 'membre': membre, 'is_member': get_is_member(request)
    })

def member_qr_code(request):
    if not require_login(request): return redirect('login')
    if request.user.is_authenticated: return redirect('index')
    
    membre = Membres.objects.get(id=request.session['membre_id'])
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(str(membre.uuid_code))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'membres/my_qr.html', {
        'membre': membre, 'qr_code': f"data:image/png;base64,{img_str}", 'is_member': get_is_member(request)
    })

def certificate(request):
    """Affiche les certificats délivrés au membre"""
    if not require_login(request): return redirect('login')

    membre_id = request.session.get('membre_id') or (request.user.id if request.user.is_authenticated else None)
    
    # 1. On récupère le membre
    if request.user.is_authenticated:
        # Cas admin (juste pour éviter le crash, même si admin n'a pas de certif)
        return render(request, 'membres/certificate.html', {'certificates': [], 'is_member': True})
    
    membre = get_object_or_404(Membres, id=membre_id)

    # 2. On récupère DIRECTEMENT les certificats existants en base de données
    # C'est le scan qui crée l'objet Certificate, donc on lui fait confiance.
    certificats_obtenus = Certificate.objects.filter(membre=membre).select_related('evenement')

    context = {
        'certificates': certificats_obtenus, 
        'is_member': True, 
        'membre': membre
    }
    return render(request, 'membres/certificate.html', context)

def ranking(request):
    if not require_login(request): return redirect('login')
    membre_id = request.session.get('membre_id')
    
    all_members_qs = Membres.objects.all().order_by('-points')
    rank = '-'
    if membre_id:
        all_ids = list(all_members_qs.values_list('id', flat=True))
        if membre_id in all_ids: rank = all_ids.index(membre_id) + 1

    membre = Membres.objects.get(id=membre_id) if membre_id else None
    return render(request, 'membres/ranking.html', {
        'membre': membre, 'my_rank': rank, 
        'top3': all_members_qs[:3], 'rest_of_list': all_members_qs[3:13],
        'is_member': get_is_member(request)
    })

# ============================================
# 3. PUBLIC
# ============================================

def team(request):
    members = TeamMember.objects.filter(actif=True)
    return render(request, 'membres/team.html', {'members': members, 'is_member': get_is_member(request)})

def announcements(request):
    if not require_login(request): return redirect('login')
    annonces = Annonce.objects.all()
    return render(request, 'membres/announcements.html', {'annonces': annonces, 'is_member': get_is_member(request)})

def events(request):
    return calendar(request)

def calendar(request):
    today = timezone.now().date()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year = today.year; month = today.month

    MOIS_FR = {1:'Janvier', 2:'Février', 3:'Mars', 4:'Avril', 5:'Mai', 6:'Juin', 7:'Juillet', 8:'Août', 9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Décembre'}
    all_events = Evenement.objects.filter(actif=True)
    cal = cal_lib.Calendar(firstweekday=6)
    month_days = []
    
    for week in cal.monthdatescalendar(year, month):
        for day in week:
            events_on_day = []
            for event in all_events:
                if event.date_debut <= day <= (event.date_debut + timedelta(days=event.nombre_jours - 1)):
                    events_on_day.append({'title': event.titre, 'css_class': 'bg-blue', 'id': event.id})
            
            month_days.append({
                'day_obj': day, 'day_number': day.day, 
                'is_current_month': (day.month == month), 'events': events_on_day, 'is_today': (day == today)
            })

    first_day = date(year, month, 1)
    return render(request, 'membres/calendar.html', {
        'current_year': year, 'current_month_name': MOIS_FR[month], 'days': month_days,
        'prev_year': (first_day - timedelta(days=1)).year, 'prev_month': (first_day - timedelta(days=1)).month,
        'next_year': (first_day + timedelta(days=32)).replace(day=1).year, 'next_month': (first_day + timedelta(days=32)).replace(day=1).month,
        'is_member': get_is_member(request)
    })

def send_application(request):
    if request.method == "POST":
        try:
            # Code d'envoi mail fictif
            messages.success(request, "Candidature transmise avec succès !")
        except Exception:
            messages.error(request, "Erreur de transmission.")
        return redirect('index')
    return redirect('index')

# ============================================
# 4. ADMIN (SCAN & PDF)
# ============================================

def scan_page(request):
    if not request.user.is_authenticated: return redirect('login')
    return render(request, 'membres/scan.html', {
        'evenements': Evenement.objects.filter(actif=True).order_by('-date_debut'),
        'is_member': get_is_member(request)
    })

@csrf_exempt
@require_http_methods(["POST"])
def scan_qr_code(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': '⛔ Admin requis'}, status=403)

    try:
        data = json.loads(request.body)
        uuid_code = data.get('uuid_code')
        evenement_id = data.get('evenement_id')
        
        try: membre = Membres.objects.get(uuid_code=uuid_code)
        except Membres.DoesNotExist: return JsonResponse({'success': False, 'message': '❌ Membre inconnu'}, status=404)
        
        try: evenement = Evenement.objects.get(id=evenement_id, actif=True)
        except Evenement.DoesNotExist: return JsonResponse({'success': False, 'message': '❌ Événement introuvable'}, status=404)
        
        jour_actuel = date.today()
        # if jour_actuel not in evenement.get_jours_evenement():
        #    return JsonResponse({'success': False, 'message': '❌ Mauvaise date'}, status=400)
        
        evenement.participants.add(membre)
        if Presence.objects.filter(membre=membre, evenement=evenement, jour=jour_actuel).exists():
            return JsonResponse({'success': False, 'message': f'⚠️ {membre.prenom} déjà scanné'}, status=400)
        
        Presence.objects.create(membre=membre, evenement=evenement, jour=jour_actuel, status='present')
        membre.points += evenement.points_par_jour
        membre.save()
        
        jours_assistes = Presence.objects.filter(membre=membre, evenement=evenement, status='present').count()
        nouveau_certificat = False
        
        if jours_assistes >= evenement.nombre_jours:
            _, created = Certificate.objects.get_or_create(
                membre=membre, evenement=evenement,
                defaults={'titre': f'Certificat - {evenement.titre}'}
            )
            nouveau_certificat = created
        
        return JsonResponse({
            'success': True, 'message': f'✅ Bienvenue {membre.prenom}!',
            'data': {'nom': f"{membre.prenom} {membre.nom}", 'points_total': membre.points, 'nouveau_certificat': nouveau_certificat}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def attendance_stats(request, evenement_id):
    if not request.user.is_authenticated: return JsonResponse({'error': 'Interdit'}, status=403)
    try:
        evt = Evenement.objects.get(id=evenement_id)
        return JsonResponse({
            'titre': evt.titre,
            'scans_total': Presence.objects.filter(evenement=evt, status='present').count(),
            'certificats_generes': Certificate.objects.filter(evenement=evt).count(),
        })
    except: return JsonResponse({'error': 'Erreur'}, status=404)

def generate_certificate_pdf(request, certificate_id):
    cert = get_object_or_404(Certificate, id=certificate_id)
    evt = cert.evenement
    membre = cert.membre

    if 'membre_id' in request.session:
        if request.session['membre_id'] != membre.id: return redirect('index')
    elif not request.user.is_authenticated:
        return redirect('login')

    template = getattr(evt, 'template_certificat', None)
    if not template: return HttpResponse("Design manquant", status=404)

    buffer = io.BytesIO()
    width, height = landscape(A4)
    p = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Fond
    if template.image_fond:
        try: p.drawImage(template.image_fond.path, 0, 0, width=width, height=height)
        except: pass
    
    # Signature
    if template.signature:
        try: p.drawImage(template.signature.path, template.sign_x, template.sign_y, width=150, height=80, mask='auto')
        except: pass

    # Texte
    font_name = "Helvetica-Bold"
    if template.police_ttf:
        try:
            custom_font = f"Font_{evt.id}"
            pdfmetrics.registerFont(TTFont(custom_font, template.police_ttf.path))
            font_name = custom_font
        except: pass

    p.setFont(font_name, template.taille_police)
    try: p.setFillColor(HexColor(template.text_color))
    except: p.setFillColor(HexColor('#000000'))
    
    p.drawCentredString(template.nom_x, template.nom_y, f"{membre.prenom} {membre.nom}")
    p.showPage()
    p.save()
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f"Certificat_{evt.titre}.pdf")

def landing(request):
    return render(request, 'membres/landing.html')

def contact(request):
    return render(request, 'membres/contact.html', {'is_member': get_is_member(request)})