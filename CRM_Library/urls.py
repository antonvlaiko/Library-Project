from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('library.urls')),
    path('users/', include('users.urls')),
    # path('library/', include('library.urls')),
]
urlpatterns += i18n_patterns(
    path('', include('library.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
