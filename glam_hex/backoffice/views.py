from django.contrib.auth.decorators import login_required

@login_required(login_url='/backoffice/login/')
def upload_about_picture_view(request):
    message = None
    error = None
    about_url = None
    # Get current about background
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM about_picture ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            about_url = row[0]
    if request.method == 'POST' and request.FILES.get('about_picture'):
        about_picture = request.FILES['about_picture']
        # Save file to media/about
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'about')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'about', about_picture.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in about_picture.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO about_picture (url) VALUES (%s)", [db_path])
        message = 'About section background uploaded!'
        about_url = db_path
    return render(request, 'backoffice/upload_about_picture.html', {'message': message, 'error': error, 'about_url': about_url})
from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required(login_url='/backoffice/login/')
def upload_banner_view(request):
    message = None
    error = None
    banner_url = None
    # Get current banner
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM banner_picture ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            banner_url = row[0]
    if request.method == 'POST' and request.FILES.get('banner'):
        banner = request.FILES['banner']
        # Save file to media/banner
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'banner')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'banner', banner.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in banner.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO banner_picture (url) VALUES (%s)", [db_path])
        message = 'Banner image uploaded!'
        banner_url = db_path
    return render(request, 'backoffice/upload_banner.html', {'message': message, 'error': error, 'banner_url': banner_url})
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import io

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('backoffice_dashboard')
    form = LoginForm(request.POST or None)
    error = None
    if request.method == 'POST':
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None and user.is_active:
                login(request, user)
                return redirect('backoffice_dashboard')
            else:
                error = "Invalid username or password."
        else:
            error = "Please fill in all fields."
    return render(request, 'backoffice/login.html', {'form': form, 'error': error})

@login_required(login_url='/backoffice/login/')
def dashboard_view(request):
    # Get last 30 days of site visits
    import datetime
    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)) for i in range(29, -1, -1)]
    labels = [d.strftime('%Y-%m-%d') for d in days]
    data = [0 for _ in days]
    with connection.cursor() as cursor:
        cursor.execute("SELECT date, count FROM site_visits WHERE date >= %s ORDER BY date", [days[0]])
        rows = cursor.fetchall()
        date_to_count = {str(row[0]): row[1] for row in rows}
        for i, d in enumerate(labels):
            if d in date_to_count:
                data[i] = date_to_count[d]
    return render(request, 'backoffice/dashboard.html', {
        'labels': labels,
        'data': data,
    })

def logout_view(request):
    logout(request)
    return redirect('backoffice_login')

@login_required(login_url='/backoffice/login/')
def manage_user_view(request):
    user = request.user
    message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Update username if changed
        if username and username != user.username:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET username=%s WHERE id=%s",
                    [username, user.id]
                )
            user.username = username
            message = 'Username updated successfully.'
        # Update password if provided
        if password:
            hashed_password = make_password(password)
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password=%s WHERE id=%s",
                    [hashed_password, user.id]
                )
            message = (message or '') + ' Password updated successfully.'
            # Re-authenticate after password change
            user.password = hashed_password
            login(request, user)
    return render(request, 'backoffice/manage_user.html', {'user': user, 'message': message})

@login_required(login_url='/backoffice/login/')
def add_user_view(request):
    message = None
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'user')
        if not username or not password or not role:
            error = 'All fields are required.'
        else:
            # Check if username already exists
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users WHERE username=%s", [username])
                if cursor.fetchone()[0] > 0:
                    error = 'Username already exists.'
                else:
                    hashed_password = make_password(password)
                    cursor.execute(
                        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                        [username, hashed_password, role]
                    )
                    message = 'User added successfully.'
    return render(request, 'backoffice/add_user.html', {'message': message, 'error': error})

@login_required(login_url='/backoffice/login/')
def add_picture_view(request):
    message = None
    error = None
    MAX_SIZE_MB = 5  # 5 MB per file
    MAX_SIZE = MAX_SIZE_MB * 1024 * 1024
    MAX_DIM = 1200  # Max width or height in pixels
    if request.method == 'POST':
        files = request.FILES.getlist('pictures')
        if not files:
            error = 'Please select at least one picture to upload.'
        else:
            saved_count = 0
            for picture in files:
                if picture.size > MAX_SIZE:
                    error = f'File {picture.name} exceeds {MAX_SIZE_MB} MB limit.'
                    continue
                # Open and resize/compress image
                try:
                    img = Image.open(picture)
                    img_format = img.format if img.format else 'JPEG'
                    # Resize if needed
                    if img.width > MAX_DIM or img.height > MAX_DIM:
                        ratio = min(MAX_DIM / img.width, MAX_DIM / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.LANCZOS)
                    # Save to buffer
                    buffer = io.BytesIO()
                    img.save(buffer, format=img_format, quality=85, optimize=True)
                    buffer.seek(0)
                except Exception as e:
                    error = f'Error processing {picture.name}: {e}'
                    continue
                # Save file to media/pictures
                save_dir = os.path.join(settings.BASE_DIR, 'media', 'pictures')
                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join('media', 'pictures', picture.name)
                abs_path = os.path.join(settings.BASE_DIR, file_path)
                with open(abs_path, 'wb+') as destination:
                    destination.write(buffer.read())
                # Save path to database
                db_path = '/' + file_path.replace('\\', '/')
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO pictures (url) VALUES (%s)", [db_path])
                saved_count += 1
            if saved_count:
                message = f'{saved_count} picture(s) uploaded and resized.'
            elif not error:
                error = 'No pictures were uploaded.'
    return render(request, 'backoffice/add_picture.html', {'message': message, 'error': error})


# Picture management (list/delete)
from django.utils import timezone

@login_required(login_url='/backoffice/login/')
def manage_pictures_view(request):
    message = None
    error = None
    # Handle deletion
    if request.method == 'POST' and 'delete_id' in request.POST:
        pic_id = request.POST.get('delete_id')
        with connection.cursor() as cursor:
            cursor.execute("SELECT url FROM pictures WHERE id=%s", [pic_id])
            row = cursor.fetchone()
            if row:
                file_path = row[0].lstrip('/')
                abs_path = os.path.join(settings.BASE_DIR, file_path)
                try:
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                    cursor.execute("DELETE FROM pictures WHERE id=%s", [pic_id])
                    message = 'Picture deleted.'
                except Exception as e:
                    error = f'Error deleting picture: {e}'
            else:
                error = 'Picture not found.'
    # List all pictures
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, url, uploaded FROM pictures ORDER BY uploaded DESC")
        rows = cursor.fetchall()
        pictures = []
        for row in rows:
            pic = {
                'id': row[0],
                'url': row[1],
                'filename': os.path.basename(row[1]),
                'uploaded': row[2] if row[2] else timezone.now(),
            }
            pictures.append(pic)
    # Get current banner
    banner_url = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM banner_picture ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            banner_url = row[0]
    # Get current about background
    about_url = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM about_picture ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            about_url = row[0]
    return render(request, 'backoffice/manage_pictures.html', {
        'pictures': pictures,
        'message': message,
        'error': error,
        'banner_url': banner_url,
        'about_url': about_url,
    })
