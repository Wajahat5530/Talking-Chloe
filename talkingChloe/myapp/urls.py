from django.urls import path
from . import views

urlpatterns = [
    path('',               views.home,              name='home'),
    path('about',          views.about,             name='about'),
    path('about/',         views.about),
    path('login',          views.login_page,        name='login'),
    path('login/',         views.login_page),
    path('logout',         views.logout_view,       name='logout'),
    path('logout/',        views.logout_view),
    path('new-chat',       views.new_chat,          name='new_chat'),
    path('auth/login',     views.auth_login_view,   name='auth_login'),
    path('auth/register',  views.auth_register_view,name='auth_register'),
    path('chat',           views.chat,              name='chat'),
    path('chat/',          views.chat),
]
