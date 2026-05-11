from django.contrib import admin
from .models import Vacancy, Candidate

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'employment_type', 'status', 'published_at']
    list_filter = ['status', 'employment_type', 'department']
    search_fields = ['title']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'vacancy', 'stage', 'rating', 'applied_at']
    list_filter = ['stage', 'vacancy__department']
    search_fields = ['first_name', 'last_name', 'email']
