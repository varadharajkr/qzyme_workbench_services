"""gromacsCommands URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from Commands import views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^commands/', views.gromacsCommands.as_view()),
    url(r'^gcommands/', views.gromacsSample.as_view()),
    url(r'^serverdetails/', views.getserverDetails.as_view()),
    url(r'^gromacs/', views.gromacs.as_view()),
    url(r'^Path_Analysis/', views.pathanalysis.as_view()),
    url(r'^mmpbsa/', views.pathanalysis.as_view()),
    url(r'^analyse_mmpbsa/', views.analyse_mmpbsa.as_view()),
    url(r'^Hello_World/', views.Hello_World.as_view()),
    url(r'^NMA/', views.NMA.as_view()),
    url(r'^Contact_Score/', views.Contact_Score.as_view()),
    url(r'^Homology_Modelling/', views.Homology_Modelling.as_view()),
    url(r'^Loop_Modelling/', views.Loop_Modelling.as_view()),
    url(r'^Complex_Simulations/', views.Complex_Simulations.as_view()),
    url(r'^MakeSubstitution/', views.MakeSubstitution.as_view()),
    url(r'^Literature_Research/', views.Literature_Research.as_view()),
    url(r'^autodock/',views.autodock.as_view()),
    url(r'^CatMec/',views.CatMec.as_view()),
    url(r'^Designer/',views.Designer.as_view()),
    url(r'^Designer_Mmpbsa_analyse/',views.Designer_Mmpbsa_analyse.as_view()),
    url(r'^grom/', views.grom),
    url(r'^get_activation_energy/', views.get_activation_energy.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
