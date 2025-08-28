from django.shortcuts import render


def home(request):
    """Home page view"""
    return render(request, 'core/home.html')


def about(request):
    """About page view"""
    return render(request, 'core/about.html')



