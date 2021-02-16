"""enif URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from enif_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="Index"),
    path('api/v1/build-dnn/', views.run_DNN_Admin, name='run_dnn'),
    path('api/v1/session/<token>', views.Enif_Session_Api.as_view()),
    path('api/v1/session/', views.Enif_Session_Api.as_view()),
    path('api/v1/request/<session>/<pk>', views.Enif_Request_Api.as_view()),
    path('api/v1/request/<session>/', views.Enif_Request_Api.as_view()),
    path('api/v1/request/', views.Enif_Request_Api.as_view()),
    path('api/v1/enif/<session>/', views.Chatbot_Api.as_view()),
]
