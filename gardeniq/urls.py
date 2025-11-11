"""gardeniq URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include
from django.urls import path

from gardeniq.base import api_urls as base_api_urls
from gardeniq.orderlg import api_urls as orderlg_api_urls

api_urlpatterns = [
    path("", include(base_api_urls)),
    path("", include(orderlg_api_urls)),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_urlpatterns)),
]

if getattr(settings, "DEBUG", False):
    from drf_spectacular.views import SpectacularAPIView
    from drf_spectacular.views import SpectacularRedocView
    from drf_spectacular.views import SpectacularSwaggerView

    # API schema:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/schema/swagger-ui/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]
