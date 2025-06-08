from django.shortcuts import render, get_object_or_404, redirect
import openpyxl
from django.http import HttpResponse
from .models import Book, Loan, Invoice, BookRating
from django.db.models import Avg
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages
from datetime import timedelta
from .forms import UserUpdateForm, UserProfileUpdateForm
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import Loan
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from .models import UserProfile
from collections import OrderedDict

def home(request):
    # search_query = request.GET.get('q', '')
    # if search_query:
    #     books = Book.objects.filter(
    #         Q(title__icontains=search_query) |
    #         Q(author__icontains=search_query) |
    #         Q(genre__icontains=search_query) |
    #         Q(isbn__icontains=search_query) |
    #         Q(published_year__icontains=search_query),
    #         visible=True
    #     )
    # else:
    #     books = Book.objects.none()  # Порожній QuerySet, якщо немає пошукового запиту
    # top_categories = Book.objects.filter(visible=True).values('genre').annotate(num_loans=Count('loan')).order_by('-num_loans')[:5]
    # newest_books = Book.objects.filter(visible=True).order_by('-created_at')[:5]
    # context = {
    #     'books': books,
    #     'top_categories': top_categories,
    #     'newest_books': newest_books,
    #     'search_query': search_query,  # Опціонально, якщо хочеш заздалегідь заповнити поле у шаблоні
    # }
    # return render(request, 'library/home.html', context)
    lang_code = get_language() or 'en'

    search_query = request.GET.get('q', '').strip()
    selected_genres = request.GET.getlist('genre_en')
    year_min = request.GET.get('year_min')
    year_max = request.GET.get('year_max')

    # Start with visible books
    books = Book.objects.filter(visible=True)
    if year_min:
        year_min_int = int(year_min)
        books = books.filter(published_year__gte=year_min_int)
    if year_max:
        year_max_int = int(year_max)
        books = books.filter(published_year__lte=year_max_int)
    # Apply search filter
    if search_query:
        books = books.filter(
            Q(title_en__icontains=search_query) |
            Q(title_uk__icontains=search_query) |
            Q(author_en__icontains=search_query) |
            Q(author_uk__icontains=search_query) |
            Q(genre_en__icontains=search_query) |
            Q(genre_uk__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(published_year__icontains=search_query)
        )

    genre_field = 'genre_uk' if lang_code == 'uk' else 'genre_en'
    selected_genres = request.GET.getlist('genre')

    if selected_genres:
        books = books.filter(
            Q(genre_en__in=selected_genres) |
            Q(genre_uk__in=selected_genres)
        )

    genres = (
        Book.objects.filter(visible=True)
        .exclude(**{f"{genre_field}__isnull": True})
        .exclude(**{f"{genre_field}__exact": ''})
        .values_list(genre_field, flat=True)
        .distinct()
        .order_by(genre_field)
    )

    # Top categories
    top_genres = (
        Book.objects.filter(visible=True)
        .exclude(genre_en__isnull=True)
        .exclude(genre_en__exact='')
        .values('genre_en')
        .annotate(num_loans=Count('loan'))
        .order_by('-num_loans')[:5]
    )
    top_categories = []

    for entry in top_genres:
        genre_en = entry['genre_en']
        # Get any book with this genre_en to use genre_localized
        book = Book.objects.filter(genre_en=genre_en, visible=True).first()
        if book:
            top_categories.append({
                'genre_localized': book.genre_localized,
                'num_loans': entry['num_loans'],
            })
    if not request.user.is_authenticated:
        similar_books = []
    else:
        # Get returned loans for logged-in user
        returned_loans = Loan.objects.filter(user=request.user, is_returned=True).select_related('book')

        similar_authors = set()
        similar_genres = set()
        books_read_ids = set()

        for loan in returned_loans:
            book = loan.book
            similar_authors.add(book.author_en)
            similar_genres.add(book.genre_en)
            books_read_ids.add(book.id)

        similar_books = Book.objects.filter(
            Q(author_en__in=similar_authors) | Q(genre_en__in=similar_genres)
        ).exclude(id__in=books_read_ids).distinct()[:8]
    # Show newest only if no filter is applied
    show_newest = not search_query and not selected_genres
    newest_books = Book.objects.filter(visible=True).order_by('-created_at')[:4] if show_newest else books

    context = {
        'books': books,
        'top_categories': top_categories,
        'newest_books': newest_books,
        'search_query': search_query,
        'year_min': year_min,
        'genres': genres,
        'genre_field': genre_field,
        'selected_genres': selected_genres,
        'show_newest': show_newest,
        'similar_books': similar_books,
        'lang_code': lang_code,
    }
    return render(request, 'library/home.html', context)


@login_required
def dashboard(request):
    my_loans = Loan.objects.filter(user=request.user, is_returned=False, is_accepted=True)
    pending_loans = Loan.objects.filter(user=request.user, is_requested=True, is_accepted=False, is_rejected=False)
    pending_returns = Loan.objects.filter(user=request.user, is_requested_to_return=True, is_returned=False)
    my_invoices = Invoice.objects.filter(user=request.user, paid=False)
    now = timezone.now()
    rejected_loans_messages = []
    for loan in my_loans:
        if loan.is_rejected and loan.rejected_at and (now - loan.rejected_at) < timedelta(minutes=10):
            rejected_loans_messages.append(loan)
    return render(request, 'library/dashboard.html', {
        'my_loans': my_loans,
        'my_invoices': my_invoices,
        'pending_loans': pending_loans,
        'pending_returns': pending_returns,
        'rejected_loans_messages': rejected_loans_messages,
    })

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk, visible=True)
    # Calculate average rating
    average_rating = BookRating.objects.filter(book=book).aggregate(avg=Avg('rating'))['avg']

    # Check if user has returned this book
    has_returned = Loan.objects.filter(user=request.user, book=book, is_returned=True).exists()

    # Check if user has already rated
    user_rating = BookRating.objects.filter(user=request.user, book=book).first()

    context = {
        'book': book,
        'average_rating': round(average_rating, 1) if average_rating else None,
        'can_rate': has_returned,
        'user_rating': user_rating.rating if user_rating else None,
        'rating_choices': [5, 4, 3, 2, 1],
    }
    return render(request, 'library/book_detail.html', context)

@login_required
def request_book(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        if book.copies_available > 0:
            existing = Loan.objects.filter(user=request.user, book=book, is_requested=True, is_accepted=False)
            if existing.exists():
                messages.warning(request, _('You have already requested this book.'))
                return redirect('dashboard')

            Loan.objects.create(
                user=request.user,
                book=book,
                is_requested=True,
                is_accepted=False
            )
            messages.info(request, _('You requested this book. Awaiting librarian approval.'))
        else:
            messages.error(request, _('No copies available'))
        return redirect('dashboard')

    return redirect('book_detail', book_id=book.id)

@login_required
def rate_book(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Check if user returned the book to allow rating
    has_returned = Loan.objects.filter(user=request.user, book=book, is_returned=True).exists()
    if not has_returned:
        messages.error(request, "You can rate this book only after returning it.")
        return redirect('book_detail', pk=pk)

    if request.method == 'POST':
        rating_value = int(request.POST.get('rating', 0))
        if 1 <= rating_value <= 5:
            # Update or create the rating
            obj, created = BookRating.objects.update_or_create(
                user=request.user,
                book=book,
                defaults={'rating': rating_value}
            )
            messages.success(request, _("Thanks for rating the book!"))
        else:
            messages.error(request, "Invalid rating value.")

    return redirect('book_detail', pk=pk)


def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    all_books = Book.objects.all()
    all_loans = Loan.objects.filter(is_returned=False)
    open_invoices = Invoice.objects.filter(paid=False)
    loan_requests = Loan.objects.filter(is_requested=True, is_accepted=False, is_rejected=False)
    return_requests = Loan.objects.filter(is_requested_to_return=True, is_returned=False)
    recently_rejected_loans = [loan for loan in loan_requests if loan.is_recently_rejected()]
    show_reject_message = bool(recently_rejected_loans)
    return render(request, 'library/admin_dashboard.html', {
        'all_books': all_books,
        'all_loans': all_loans,
        'open_invoices': open_invoices,
        'loan_requests': loan_requests,
        'return_requests': return_requests,
        'show_reject_message': show_reject_message,
    })

@login_required
@user_passes_test(is_admin)
def accept_loan(request, loan_id):
    if request.method == 'POST':
        loan = get_object_or_404(Loan, id=loan_id)

        if loan.book.copies_available > 0:
            loan.is_accepted = True
            loan.borrowed_at = timezone.now()
            loan.due_date = timezone.now() + timedelta(days=14)
            loan.save()
            loan.book.copies_available -= 1
            loan.book.save()
            messages.success(request, _('Loan approved successfully.'))
        else:
            messages.error(request, _('No copies available.'))

    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def accept_return(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, is_requested_to_return=True, is_returned=False)

    loan.is_returned = True
    loan.book.copies_available += 1
    loan.book.save()
    loan.save()

    # Calculate overdue and invoice
    free_period = timedelta(days=14)
    borrowed_for = loan.returned_at - loan.borrowed_at
    if borrowed_for > free_period:
        days_overdue = (borrowed_for - free_period).days
        amount = 1.5 * days_overdue
        Invoice.objects.create(
            user=loan.user,
            book=loan.book,
            amount=amount,
            due_date=timezone.now()
        )

    messages.success(request, _('The return has been accepted.'))
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def add_book(request):
    if request.method == 'POST':
        isbn = request.POST['isbn']
        title_uk = request.POST['title_uk']
        title_en = request.POST['title_en']
        author_uk = request.POST['author_uk']
        author_en = request.POST['author_en']
        genre_uk = request.POST['genre_uk']
        genre_en = request.POST['genre_en']
        published_year = request.POST['published_year']
        copies_available = request.POST['copies_available']
        # Коректне перетворення чекбокса у булеве значення:
        visible = request.POST.get('visible') == 'on'
        image = request.FILES.get('image')
        Book.objects.create(
            isbn=isbn, title_en=title_en, title_uk=title_uk, author_en=author_en, author_uk=author_uk, genre_en=genre_en, genre_uk=genre_uk,
            published_year=published_year, copies_available=copies_available,
            visible=visible, image=image
        )
        messages.success(request, _('The book was added!'))
        return redirect('admin_dashboard')
    return render(request, 'library/add_book.html')

@login_required
def return_book(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, user=request.user, is_returned=False)

    if request.method == 'POST':
        loan.is_requested_to_return = True
        loan.returned_at = timezone.now()
        loan.save()
        messages.success(request, _('Return request submitted. Please wait for librarian approval.'))
        return redirect('dashboard')

@login_required
def pay_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user, paid=False)
    if request.method == 'POST':
        invoice.paid = True
        invoice.save()
        messages.success(request, _('Invoice paid!'))
        return redirect('dashboard')
    return render(request, 'library/pay_invoice.html', {'invoice': invoice})

@login_required
@user_passes_test(is_admin)
def book_database(request):
    query = request.GET.get('q', '')  # get search query from ?q=

    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(title_en__icontains=query) |
            Q(title_uk__icontains=query) |
            Q(author_en__icontains=query) |
            Q(author_uk__icontains=query) |
            Q(genre_en__icontains=query) |
            Q(genre_uk__icontains=query) |
            Q(isbn__icontains=query) |
            Q(published_year__icontains=query)
        )
    return render(request, 'library/book_database.html', {'books': books, 'query': query})


@login_required
@user_passes_test(is_admin)
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.title_uk = request.POST.get('title_uk', book.title_uk)
        book.title_en = request.POST.get('title_en', book.title_en)
        book.author_uk = request.POST.get('author_uk', book.author_uk)
        book.author_en = request.POST.get('author_en', book.author_en)
        book.genre_uk = request.POST.get('genre_uk', book.genre_uk)
        book.genre_en = request.POST.get('genre_en', book.genre_en)
        book.isbn = request.POST.get('isbn', book.isbn)
        book.published_year = request.POST.get('published_year', book.published_year)
        book.copies_available = int(request.POST.get('copies_available', book.copies_available))
        # Для чекбокса:
        book.visible = request.POST.get('visible') == 'on'
        book.save()
        messages.success(request, _('The book was successfully edited!'))
        return redirect('book_database')
    return render(request, 'library/edit_book.html', {'book': book})

@login_required
@user_passes_test(is_admin)
def all_loans(request):
    # Всі позики, відсортовані за статусом повернення, останні спочатку
    today = timezone.now().date()
    query = request.GET.get('q', '').strip()

    # Load loans
    loans = Loan.objects.select_related('book', 'user').order_by('-borrowed_at')

    # Filter by search query
    if query:
        loans = loans.filter(
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query)
        )

    # Compute extra fields (overdue, fee)
    for loan in loans:
        loan.due_date_date = loan.due_date.date() if loan.due_date else None
        if not loan.is_returned and loan.due_date_date and today > loan.due_date_date:
            loan.days_overdue = (today - loan.due_date_date).days
            loan.fee = round(loan.days_overdue * 1.5, 2)
        else:
            loan.days_overdue = 0
            loan.fee = 0

    # Handle Excel export
    if request.GET.get('export') == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Loans"

        headers = [
            str(_("Book")), str(_("ISBN")), str(_("Author (English)")), str(_("Genre (English)")), str(_("Year of publishing")),
            str(_("User")), str(_("Lent")), str(_("Until")), str(_("Returned")),
            str(_("Late by (days)")), str(_("Fee (€)"))
        ]
        ws.append(headers)

        for loan in loans:
            row = [
                loan.book.title_localized if hasattr(loan.book, 'title_localized') else loan.book.title_en,
                loan.book.isbn,
                loan.book.author_en,
                loan.book.genre_en,
                loan.book.published_year,
                loan.user.username,
                loan.borrowed_at.strftime("%d.%m.%Y %H:%M") if loan.borrowed_at else '',
                loan.due_date.strftime("%d.%m.%Y %H:%M") if loan.due_date else '',
                loan.returned_at.strftime("%d.%m.%Y %H:%M") if loan.is_returned and loan.returned_at else str(_('No')),
                loan.days_overdue,
                f"{loan.fee:.2f} €"
            ]
            ws.append(row)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename=loans.xlsx'
        wb.save(response)
        return response

    # Normal render
    return render(request, 'library/all_loans.html', {
        'loans': loans,
        'query': query,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Profile was updated!'))
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileUpdateForm(instance=request.user.profile)

    loan_history = Loan.objects.filter(user=request.user).select_related('book').order_by('-returned_at')
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'loan_history': loan_history,
    }
    return render(request, 'library/profile.html', context)


@login_required
@user_passes_test(is_admin)
def reject_loan(request, loan_id):
    if request.method == "POST":
        loan = get_object_or_404(Loan, id=loan_id, is_rejected=False)
        loan.is_rejected = True
        loan.rejected_at = timezone.now()
        loan.save()

        messages.error(request, _("Loan was rejected."))

    return redirect("admin_dashboard")
