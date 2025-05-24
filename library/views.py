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
from .forms import UserUpdateForm
from django.utils.translation import gettext as _

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
    search_query = request.GET.get('q', '').strip()
    selected_genres = request.GET.getlist('genre')
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
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(genre__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(published_year__icontains=search_query)
        )

    # Apply genre filter
    if selected_genres:
        books = books.filter(genre__in=selected_genres)

    # Get all genres for checkbox list
    genres = (
        Book.objects.filter(visible=True)
        .exclude(genre__isnull=True)
        .exclude(genre__exact='')
        .values_list('genre', flat=True)
        .distinct()
        .order_by('genre')
    )

    # Top categories
    top_categories = (
        Book.objects.filter(visible=True)
        .exclude(genre__isnull=True)
        .exclude(genre__exact='')
        .values('genre')
        .annotate(num_loans=Count('loan'))
        .order_by('-num_loans')[:5]
    )
    if not request.user.is_authenticated:
        # Show some default content or empty recommendations for anonymous users
        similar_books = []  # or maybe popular books, etc.
    else:
        # Get returned loans for logged-in user
        returned_loans = Loan.objects.filter(user=request.user, is_returned=True).select_related('book')

        similar_authors = set()
        similar_genres = set()
        books_read_ids = set()

        for loan in returned_loans:
            book = loan.book
            similar_authors.add(book.author)
            similar_genres.add(book.genre)
            books_read_ids.add(book.id)

        similar_books = Book.objects.filter(
            Q(author__in=similar_authors) | Q(genre__in=similar_genres)
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
        'selected_genres': selected_genres,
        'show_newest': show_newest,
        'similar_books': similar_books,
    }
    return render(request, 'library/home.html', context)


@login_required
def dashboard(request):
    my_loans = Loan.objects.filter(user=request.user, is_returned=False)
    my_invoices = Invoice.objects.filter(user=request.user, paid=False)
    return render(request, 'library/dashboard.html', {
        'my_loans': my_loans,
        'my_invoices': my_invoices,
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



    if request.method == 'POST':
        if book.copies_available > 0:
            due = timezone.now() + timedelta(days=14)
            Loan.objects.create(user=request.user, book=book, due_date=due)
            book.copies_available -= 1
            book.save()
            messages.success(request, _('The book was lent successfuly!'))
            return redirect('dashboard')
        else:
            messages.error(request, _('No copies available'))
    context = {
        'book': book,
        'average_rating': round(average_rating, 1) if average_rating else None,
        'can_rate': has_returned,
        'user_rating': user_rating.rating if user_rating else None,
        'rating_choices': [5, 4, 3, 2, 1],
    }
    return render(request, 'library/book_detail.html', context)


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
            messages.success(request, f"Thanks for rating {book.title}!")
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
    return render(request, 'library/admin_dashboard.html', {
        'all_books': all_books,
        'all_loans': all_loans,
        'open_invoices': open_invoices,
    })

@login_required
@user_passes_test(is_admin)
def add_book(request):
    if request.method == 'POST':
        isbn = request.POST['isbn']
        title = request.POST['title']
        author = request.POST['author']
        genre = request.POST['genre']
        published_year = request.POST['published_year']
        copies_available = request.POST['copies_available']
        # Коректне перетворення чекбокса у булеве значення:
        visible = request.POST.get('visible') == 'on'
        image = request.FILES.get('image')
        Book.objects.create(
            isbn=isbn, title=title, author=author, genre=genre,
            published_year=published_year, copies_available=copies_available,
            visible=visible, image=image
        )
        messages.success(request, _('The book was added!'))
        return redirect('admin_dashboard')
    return render(request, 'library/add_book.html')

@login_required
def return_book(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, user=request.user, is_returned=False)
    loan.is_returned = True
    loan.returned_at = timezone.now()
    loan.book.copies_available += 1
    loan.book.save()
    loan.save()

    # Обчислити 14-денний строк
    free_period = timedelta(days=14)
    borrowed_for = loan.returned_at - loan.borrowed_at
    if borrowed_for > free_period:
        days_overdue = (borrowed_for - free_period).days
        amount = 1.5 * days_overdue
        Invoice.objects.create(
            user=request.user,
            book=loan.book,
            amount=amount,
            due_date=timezone.now()
        )
    messages.success(request, _('The book was returned!'))
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
    books = Book.objects.all()
    return render(request, 'library/book_database.html', {'books': books})


@login_required
@user_passes_test(is_admin)
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.title = request.POST.get('title', book.title)
        book.author = request.POST.get('author', book.author)
        book.genre = request.POST.get('genre', book.genre)
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
    loans = Loan.objects.select_related('book', 'user').order_by('-borrowed_at')
    today = timezone.now().date()

    # Обчислення додаткових полів (must come before export)
    for loan in loans:
        loan.due_date_date = loan.due_date.date()
        if not loan.is_returned and today > loan.due_date_date:
            loan.days_overdue = (today - loan.due_date_date).days
            loan.fee = round(loan.days_overdue * 1.5, 2)
        else:
            loan.days_overdue = 0
            loan.fee = 0

    # Excel export
    if request.GET.get('export') == 'excel':
        import openpyxl
        from django.http import HttpResponse

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Loans"

        headers = [
            _("Book"), _("ISBN"), _("Author"), _("Genre"), _("Year of publishing"),
            _("User"), _("Lent"), _("Until"), _("Returned"),
            _("Late by (days)"), _("Fee (€)")
        ]
        ws.append(headers)

        for loan in loans:
            row = [
                loan.book.title,
                loan.book.isbn,
                loan.book.author,
                loan.book.genre,
                loan.book.published_year,
                loan.user.username,
                loan.borrowed_at.strftime("%d.%m.%Y %H:%M") if loan.borrowed_at else '',
                loan.due_date.strftime("%d.%m.%Y %H:%M") if loan.due_date else '',
                loan.returned_at.strftime("%d.%m.%Y %H:%M") if loan.is_returned and loan.returned_at else 'Ні',
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
    return render(request, 'library/all_loans.html', {'loans': loans})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile was updated!'))
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    loan_history = Loan.objects.filter(user=request.user).select_related('book').order_by('-returned_at')
    context = {
        'form': form,
        'loan_history': loan_history,
    }
    return render(request, 'library/profile.html', context)