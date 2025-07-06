from django.shortcuts import render
from django.db import connection
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

def home_view(request):
    # Track site visit (per day)
    from datetime import date
    today = date.today()
    with connection.cursor() as cursor:
        cursor.execute("SELECT count FROM site_visits WHERE date=%s", [today])
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE site_visits SET count = count + 1 WHERE date=%s", [today])
        else:
            cursor.execute("INSERT INTO site_visits (date, count) VALUES (%s, 1)", [today])
    # Load pictures from the database (assuming a 'pictures' table with a 'url' column)
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM pictures")
        pictures = [{'url': row[0]} for row in cursor.fetchall()]
    # Load banner image (latest)
    banner_url = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM banner_picture ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            banner_url = row[0]
    # Load about section background (latest)
    about_url = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM about_picture ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            about_url = row[0]
    contact_message = None
    contact_error = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        if not name or not email or not message:
            contact_error = 'All fields are required.'
        else:
            send_mail(
                subject=f'Contact from {name}',
                message=message + f"\n\nFrom: {name} <{email}>",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
            )
            contact_message = 'Your message has been sent!'
    return render(request, 'frontoffice/home.html', {
        'pictures': pictures,
        'banner_url': banner_url,
        'about_url': about_url,
        'contact_message': contact_message,
        'contact_error': contact_error,
    })

def about_view(request):
    return render(request, 'frontoffice/about.html')
