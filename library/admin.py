from django.contrib import admin
from .models import Book, Loan, Invoice, BookRating

admin.site.register(Book)
admin.site.register(Loan)
admin.site.register(Invoice)
admin.site.register(BookRating)
