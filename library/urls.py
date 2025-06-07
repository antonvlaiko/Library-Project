from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/request-book/', views.request_book, name='request_book'),
    path('book/<int:pk>/rate/', views.rate_book, name='rate_book'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('accept-loan/<int:loan_id>/', views.accept_loan, name='accept_loan'),
    path('reject-loan/<int:loan_id>/', views.reject_loan, name='reject_loan'),
    path('request-return/<int:loan_id>/', views.return_book, name='return_book'),
    path('accept-return/<int:loan_id>/', views.accept_return, name='accept_return'),

    path('add-book/', views.add_book, name='add_book'),
    path('return-book/<int:loan_id>/', views.return_book, name='return_book'),
    path('pay-invoice/<int:invoice_id>/', views.pay_invoice, name='pay_invoice'),
    path('datenbank/', views.book_database, name='book_database'),
    path('books/edit_book/<int:book_id>/', views.edit_book, name='edit_book'),
    path('all-loans/', views.all_loans, name='all_loans'),
    path('profile/', views.profile, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)