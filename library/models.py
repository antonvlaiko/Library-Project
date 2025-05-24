from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Book(models.Model):
    isbn = models.CharField(_("ISBN"), max_length=50, unique=True)
    title = models.CharField(_("Title"), max_length=200)
    author = models.CharField(_("Author"), max_length=100)
    genre = models.CharField(_("Genre"), max_length=100)
    published_year = models.PositiveIntegerField(_("Published Year"))
    copies_available = models.PositiveIntegerField(_("Copies Available"))
    visible = models.BooleanField(_("Visible"), default=True)
    image = models.ImageField(_("Book Cover"), upload_to='book_images/', blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")

    def __str__(self):
        return self.title

class Loan(models.Model):
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    book = models.ForeignKey(Book, verbose_name=_("Book"), on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(_("Borrowed At"), auto_now_add=True)
    due_date = models.DateTimeField(_("Due Date"))
    returned_at = models.DateTimeField(_("Returned At"), null=True, blank=True)
    is_returned = models.BooleanField(_("Returned"), default=False)

    class Meta:
        verbose_name = _("Loan")
        verbose_name_plural = _("Loans")

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Invoice(models.Model):
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    book = models.ForeignKey(Book, verbose_name=_("Book"), on_delete=models.CASCADE)
    amount = models.DecimalField(_("Amount (€)"), max_digits=6, decimal_places=2)
    due_date = models.DateTimeField(_("Due Date"))
    paid = models.BooleanField(_("Paid"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

class BookRating(models.Model):
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    book = models.ForeignKey(Book, verbose_name=_("Book"), on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('user', 'book')
        verbose_name = _("Book Rating")
        verbose_name_plural = _("Book Ratings")
