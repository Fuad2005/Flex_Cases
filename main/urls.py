from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-case/', views.create_case, name='create-case'),
    path('all-cases/', views.all_cases, name='all-cases'),
    path('case/<int:case_id>/', views.case_detail, name='case-detail'),
    path('case/<int:case_id>/update/', views.update_case, name='update-case'),
    path('case/<int:case_id>/delete/', views.delete_case, name='delete-case'),
    path('staff/', views.staff, name='staff'),
]
