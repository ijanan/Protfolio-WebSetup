from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('project/<slug:slug>/', views.project_detail, name='project_detail'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('contact/', views.contact_submit, name='contact_submit'),
    path('download-resume/', views.download_resume, name='download_resume'),
]
