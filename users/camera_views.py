def process_camera_photo(photo_data):
    """Process a base64 photo from the camera capture form.
    Returns a ContentFile ready to be saved to an ImageField."""
    import base64
    from django.core.files.base import ContentFile
    
    # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
    if ';base64,' in photo_data:
        header, photo_data = photo_data.split(';base64,')
    
    # Decode base64 to binary
    image_data = base64.b64decode(photo_data)
    return ContentFile(image_data, name='profile_photo.jpg')


def camera_capture(request):
    """Handle camera photo capture and save to user profile."""
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import redirect
    from django.contrib import messages
    
    @login_required
    def inner(request):
        if request.method == 'POST':
            photo_data = request.POST.get('photo_data')
            if photo_data:
                try:
                    # Process and save the photo
                    photo_file = process_camera_photo(photo_data)
                    request.user.profile_photo.save('profile.jpg', photo_file, save=True)
                    messages.success(request, 'Profile photo saved successfully!')
                    
                    # If this was during registration, proceed to next step
                    next_url = request.GET.get('next', 'jobs:job_list')
                    return redirect(next_url)
                except Exception as e:
                    messages.error(request, 'Could not save photo. Please try again.')
                    print(f'Photo save error: {e}')
            else:
                messages.error(request, 'No photo data received. Please try again.')
        
        return render(request, 'users/camera_capture.html')
    
    return inner(request)