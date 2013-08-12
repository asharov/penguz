from django.contrib import admin
from penguz.app.models import Contest, Puzzle, Participation, Answer, UserProfile

admin.site.register(Contest)
admin.site.register(Puzzle)
admin.site.register(Participation)
admin.site.register(Answer)
admin.site.register(UserProfile)
