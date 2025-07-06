from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def get_sidebar_next_appointment():
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT title, start, end, description FROM appointments WHERE start > NOW() ORDER BY start ASC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return {
                'title': row[0],
                'start': row[1],
                'end': row[2],
                'description': row[3],
            }
    return None

@login_required(login_url='/backoffice/login/')
def calendar_export_ics(request):
    from django.db import connection
    response = HttpResponse(content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename="appointments.ics"'
    response.write('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//GlamHex//EN\r\n')
    with connection.cursor() as cursor:
        cursor.execute("SELECT title, start, end, description FROM appointments")
        for title, start, end, description in cursor.fetchall():
            response.write('BEGIN:VEVENT\r\n')
            response.write(f'SUMMARY:{title}\r\n')
            response.write(f'DTSTART:{start.strftime("%Y%m%dT%H%M%S")}\r\n')
            response.write(f'DTEND:{end.strftime("%Y%m%dT%H%M%S")}\r\n')
            if description:
                response.write(f'DESCRIPTION:{description}\r\n')
            response.write('END:VEVENT\r\n')
    response.write('END:VCALENDAR\r\n')
    return response

@login_required(login_url='/backoffice/login/')
def calendar_view(request):
    import json
    from django.http import JsonResponse
    if request.method == 'GET' and request.GET.get('fetch') == '1':
        # Return all appointments as JSON for JS calendar
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, title, start, end, description FROM appointments")
            events = [
                {
                    'id': row[0],
                    'title': row[1],
                    'start': row[2].strftime('%Y-%m-%dT%H:%M'),
                    'end': row[3].strftime('%Y-%m-%dT%H:%M'),
                    'description': row[4] or ''
                }
                for row in cursor.fetchall()
            ]
        return JsonResponse(events, safe=False)
    message = None
    error = None
    # Handle edit/delete/new appointment
    if request.method == 'POST':
        # Delete
        if request.POST.get('delete') and request.POST.get('id'):
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM appointments WHERE id=%s", [request.POST['id']])
            return JsonResponse({'deleted': True})
        # Edit
        elif request.POST.get('edit') and request.POST.get('id'):
            title = request.POST.get('title')
            start = request.POST.get('start')
            end = request.POST.get('end')
            description = request.POST.get('description')
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE appointments SET title=%s, start=%s, end=%s, description=%s WHERE id=%s",
                    [title, start, end, description, request.POST['id']]
                )
            return JsonResponse({'updated': True})
        # New
        else:
            title = request.POST.get('title')
            start = request.POST.get('start')
            end = request.POST.get('end')
            description = request.POST.get('description')
            if not title or not start or not end:
                error = 'Title, start, and end are required.'
            else:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO appointments (title, start, end, description) VALUES (%s, %s, %s, %s)",
                        [title, start, end, description]
                    )
                message = 'Appointment added.'
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/calendar.html', {'message': message, 'error': error, 'sidebar_next_appointment': sidebar_next_appointment})

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
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_about_picture.html', {'message': message, 'error': error, 'about_url': about_url, 'sidebar_next_appointment': sidebar_next_appointment})
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
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_banner.html', {'message': message, 'error': error, 'banner_url': banner_url, 'sidebar_next_appointment': sidebar_next_appointment})
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
    # Get next appointment
    next_appointment = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT title, start, end, description FROM appointments WHERE start > NOW() ORDER BY start ASC LIMIT 1")
        row = cursor.fetchone()
        if row:
            next_appointment = {
                'title': row[0],
                'start': row[1],
                'end': row[2],
                'description': row[3],
            }
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/dashboard.html', {
        'labels': labels,
        'data': data,
        'next_appointment': next_appointment,
        'sidebar_next_appointment': next_appointment,
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
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/manage_user.html', {'user': user, 'message': message, 'sidebar_next_appointment': sidebar_next_appointment})

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
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/add_user.html', {'message': message, 'error': error, 'sidebar_next_appointment': sidebar_next_appointment})

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
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/add_picture.html', {'message': message, 'error': error, 'sidebar_next_appointment': sidebar_next_appointment})


# Picture management (list/delete)
from django.utils import timezone

@login_required(login_url='/backoffice/login/')
def manage_pictures_view(request):
    message = None
    error = None
    # Handle single and bulk deletion for all galleries
    if request.method == 'POST':
        # Main gallery (pictures table)
        if 'delete_ids' in request.POST and request.POST.get('gallery_type', 'main') == 'main':
            delete_ids = request.POST.getlist('delete_ids')
            if delete_ids:
                deleted_count = 0
                with connection.cursor() as cursor:
                    for pic_id in delete_ids:
                        cursor.execute("SELECT url FROM pictures WHERE id=%s", [pic_id])
                        row = cursor.fetchone()
                        if row:
                            file_path = row[0].lstrip('/')
                            abs_path = os.path.join(settings.BASE_DIR, file_path)
                            try:
                                if os.path.exists(abs_path):
                                    os.remove(abs_path)
                                cursor.execute("DELETE FROM pictures WHERE id=%s", [pic_id])
                                deleted_count += 1
                            except Exception as e:
                                error = f'Error deleting picture: {e}'
                                break
                    if deleted_count:
                        message = f'{deleted_count} picture(s) deleted.'
                    elif not error:
                        error = 'No pictures deleted.'
        # Single delete (fallback for old forms)
        elif 'delete_id' in request.POST:
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
        # Other galleries
        else:
            # Map form POST to table
            gallery_map = {
                'social_makeup': 'social_makeup_pictures',
                'glow': 'glow_pictures',
                'mature': 'mature_pictures',
                'natural': 'natural_pictures',
                'artistic': 'artistic_pictures',
                'videoclip': 'videoclip_pictures',
            }
            for gallery_key, table in gallery_map.items():
                if f'delete_{gallery_key}' in request.POST or (request.POST.get('gallery_type') == gallery_key):
                    delete_ids = request.POST.getlist('delete_ids')
                    if delete_ids:
                        deleted_count = 0
                        with connection.cursor() as cursor:
                            for pic_id in delete_ids:
                                cursor.execute(f"SELECT url FROM {table} WHERE id=%s", [pic_id])
                                row = cursor.fetchone()
                                if row:
                                    file_path = row[0].lstrip('/')
                                    abs_path = os.path.join(settings.BASE_DIR, file_path)
                                    try:
                                        if os.path.exists(abs_path):
                                            os.remove(abs_path)
                                        cursor.execute(f"DELETE FROM {table} WHERE id=%s", [pic_id])
                                        deleted_count += 1
                                    except Exception as e:
                                        error = f'Error deleting picture: {e}'
                                        break
                            if deleted_count:
                                message = f'{deleted_count} picture(s) deleted.'
                            elif not error:
                                error = 'No pictures deleted.'
                    break
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
    # Get new gallery pictures (with id for delete)
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, url FROM social_makeup_pictures ORDER BY uploaded DESC")
        social_makeup_pictures = [{'id': row[0], 'url': row[1]} for row in cursor.fetchall()]
        cursor.execute("SELECT id, url FROM glow_pictures ORDER BY uploaded DESC")
        glow_pictures = [{'id': row[0], 'url': row[1]} for row in cursor.fetchall()]
        cursor.execute("SELECT id, url FROM mature_pictures ORDER BY uploaded DESC")
        mature_pictures = [{'id': row[0], 'url': row[1]} for row in cursor.fetchall()]
        cursor.execute("SELECT id, url FROM natural_pictures ORDER BY uploaded DESC")
        natural_pictures = [{'id': row[0], 'url': row[1]} for row in cursor.fetchall()]
        cursor.execute("SELECT id, url FROM artistic_pictures ORDER BY uploaded DESC")
        artistic_pictures = [{'id': row[0], 'url': row[1]} for row in cursor.fetchall()]
        cursor.execute("SELECT id, url FROM videoclip_pictures ORDER BY uploaded DESC")
        videoclip_pictures = [{'id': row[0], 'url': row[1]} for row in cursor.fetchall()]

    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/manage_pictures.html', {
        'pictures': pictures,
        'message': message,
        'error': error,
        'banner_url': banner_url,
        'about_url': about_url,
        'sidebar_next_appointment': sidebar_next_appointment,
        'social_makeup_pictures': social_makeup_pictures,
        'glow_pictures': glow_pictures,
        'mature_pictures': mature_pictures,
        'natural_pictures': natural_pictures,
        'artistic_pictures': artistic_pictures,
        'videoclip_pictures': videoclip_pictures,

    })

@login_required(login_url='/backoffice/login/')
def upload_social_makeup_picture_view(request):
    message = None
    error = None
    social_url = None
    # Handle delete
    if request.method == 'POST' and (request.POST.getlist('delete_ids') or request.POST.get('delete_id')):
        from .views import delete_gallery_picture
        message, error = delete_gallery_picture(request, 'social_makeup_pictures')
    # Get current social makeup picture
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM social_makeup_pictures ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            social_url = row[0]
    if request.method == 'POST' and request.FILES.get('social_picture'):
        social_picture = request.FILES['social_picture']
        # Save file to media/social_makeup
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'social_makeup')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'social_makeup', social_picture.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in social_picture.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO social_makeup_pictures (url) VALUES (%s)", [db_path])
        message = 'Social makeup picture uploaded!'
        social_url = db_path
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_social_makeup_picture.html', {'message': message, 'error': error, 'social_url': social_url, 'sidebar_next_appointment': sidebar_next_appointment})

@login_required(login_url='/backoffice/login/')
def upload_glow_picture_view(request):
    message = None
    error = None
    glow_url = None
    # Handle delete
    if request.method == 'POST' and (request.POST.getlist('delete_ids') or request.POST.get('delete_id')):
        from .views import delete_gallery_picture
        message, error = delete_gallery_picture(request, 'glow_pictures')
    # Get current glow picture
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM glow_pictures ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            glow_url = row[0]
    if request.method == 'POST' and request.FILES.get('glow_picture'):
        glow_picture = request.FILES['glow_picture']
        # Save file to media/glow
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'glow')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'glow', glow_picture.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in glow_picture.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO glow_pictures (url) VALUES (%s)", [db_path])
        message = 'Glow picture uploaded!'
        glow_url = db_path
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_glow_picture.html', {'message': message, 'error': error, 'glow_url': glow_url, 'sidebar_next_appointment': sidebar_next_appointment})

@login_required(login_url='/backoffice/login/')
def upload_mature_picture_view(request):
    message = None
    error = None
    mature_url = None
    # Handle delete
    if request.method == 'POST' and (request.POST.getlist('delete_ids') or request.POST.get('delete_id')):
        from .views import delete_gallery_picture
        message, error = delete_gallery_picture(request, 'mature_pictures')
    # Get current mature picture
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM mature_pictures ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            mature_url = row[0]
    if request.method == 'POST' and request.FILES.get('mature_picture'):
        mature_picture = request.FILES['mature_picture']
        # Save file to media/mature
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'mature')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'mature', mature_picture.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in mature_picture.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO mature_pictures (url) VALUES (%s)", [db_path])
        message = 'Mature picture uploaded!'
        mature_url = db_path
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_mature_picture.html', {'message': message, 'error': error, 'mature_url': mature_url, 'sidebar_next_appointment': sidebar_next_appointment})

@login_required(login_url='/backoffice/login/')
def upload_natural_picture_view(request):
    message = None
    error = None
    natural_url = None
    # Handle delete
    if request.method == 'POST' and (request.POST.getlist('delete_ids') or request.POST.get('delete_id')):
        from .views import delete_gallery_picture
        message, error = delete_gallery_picture(request, 'natural_pictures')
    # Get current natural picture
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM natural_pictures ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            natural_url = row[0]
    if request.method == 'POST' and request.FILES.get('natural_picture'):
        natural_picture = request.FILES['natural_picture']
        # Save file to media/natural
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'natural')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'natural', natural_picture.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in natural_picture.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO natural_pictures (url) VALUES (%s)", [db_path])
        message = 'Natural picture uploaded!'
        natural_url = db_path
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_natural_picture.html', {'message': message, 'error': error, 'natural_url': natural_url, 'sidebar_next_appointment': sidebar_next_appointment})

@login_required(login_url='/backoffice/login/')
def upload_artistic_picture_view(request):
    message = None
    error = None
    artistic_url = None
    # Handle delete
    if request.method == 'POST' and (request.POST.getlist('delete_ids') or request.POST.get('delete_id')):
        from .views import delete_gallery_picture
        message, error = delete_gallery_picture(request, 'artistic_pictures')
    # Get current artistic picture
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM artistic_pictures ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            artistic_url = row[0]
    if request.method == 'POST' and request.FILES.get('artistic_picture'):
        artistic_picture = request.FILES['artistic_picture']
        # Save file to media/artistic
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'artistic')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'artistic', artistic_picture.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in artistic_picture.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO artistic_pictures (url) VALUES (%s)", [db_path])
        message = 'Artistic picture uploaded!'
        artistic_url = db_path
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_artistic_picture.html', {'message': message, 'error': error, 'artistic_url': artistic_url, 'sidebar_next_appointment': sidebar_next_appointment})

@login_required(login_url='/backoffice/login/')
def upload_videoclip_picture_view(request):
    message = None
    error = None
    videoclip_url = None
    # Handle delete
    if request.method == 'POST' and (request.POST.getlist('delete_ids') or request.POST.get('delete_id')):
        from .views import delete_gallery_picture
        message, error = delete_gallery_picture(request, 'videoclip_pictures')
    # Get current videoclip picture
    with connection.cursor() as cursor:
        cursor.execute("SELECT url FROM videoclip_pictures ORDER BY uploaded DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            videoclip_url = row[0]
    if request.method == 'POST' and request.FILES.get('videoclip_picture'):
        videoclip_picture = request.FILES['videoclip_picture']
        # Save file to media/videoclip
        save_dir = os.path.join(settings.BASE_DIR, 'media', 'videoclip')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join('media', 'videoclip', videoclip_picture.name)
        abs_path = os.path.join(settings.BASE_DIR, file_path)
        with open(abs_path, 'wb+') as destination:
            for chunk in videoclip_picture.chunks():
                destination.write(chunk)
        db_path = '/' + file_path.replace('\\', '/')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO videoclip_pictures (url) VALUES (%s)", [db_path])
        message = 'Videoclip picture uploaded!'
        videoclip_url = db_path
    sidebar_next_appointment = get_sidebar_next_appointment()
    return render(request, 'backoffice/upload_videoclip_picture.html', {'message': message, 'error': error, 'videoclip_url': videoclip_url, 'sidebar_next_appointment': sidebar_next_appointment})

@login_required(login_url='/backoffice/login/')
def delete_gallery_picture(request, table, id_field='id'):
    # Generic delete for gallery tables
    message = None
    error = None
    if request.method == 'POST':
        delete_ids = request.POST.getlist('delete_ids')
        if delete_ids:
            deleted_count = 0
            with connection.cursor() as cursor:
                for pic_id in delete_ids:
                    cursor.execute(f"SELECT url FROM {table} WHERE {id_field}=%s", [pic_id])
                    row = cursor.fetchone()
                    if row:
                        file_path = row[0].lstrip('/')
                        abs_path = os.path.join(settings.BASE_DIR, file_path)
                        try:
                            if os.path.exists(abs_path):
                                os.remove(abs_path)
                            cursor.execute(f"DELETE FROM {table} WHERE {id_field}=%s", [pic_id])
                            deleted_count += 1
                        except Exception as e:
                            error = f'Error deleting picture: {e}'
                            break
                if deleted_count:
                    message = f'{deleted_count} picture(s) deleted.'
                elif not error:
                    error = 'No pictures deleted.'
    return message, error
