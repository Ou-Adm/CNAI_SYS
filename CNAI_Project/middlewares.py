from django.shortcuts import redirect
from django.urls import reverse

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # URLs autorisées sans restriction
        self.admin_url = reverse('admin:index')

    def __call__(self, request):
        if request.path.startswith('/admin'):
            if not request.user.is_authenticated or not request.user.is_superuser:
                return redirect('/')  # redirection vers l’accueil
        return self.get_response(request)
