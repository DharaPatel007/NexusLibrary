from django.urls import path
from . import views
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('history/', views.history, name='history'),
    path('search/', views.search_items, name='search_items'),
    path('explore/', views.explore, name='explore'),
    path('borrow/<str:item_type>/<int:item_id>/', views.borrow_item, name='borrow_item'),
    path('request/<int:item_id>/', views.request_item, name='request_item'),
    path('return/<str:item_type>/<int:item_id>/', views.return_item, name='return_item'),
    path('password-reset/', PasswordResetView.as_view(template_name='library/password_reset.html'), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='library/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='library/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='library/password_reset_complete.html'), name='password_reset_complete'),
    path('reserve/<int:item_id>/', views.reserve_book, name='reserve_book'),
]