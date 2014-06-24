from django.conf import settings

def admin_email(request):
    return { 'ADMIN_EMAIL': settings.ADMINS[0][1] }
