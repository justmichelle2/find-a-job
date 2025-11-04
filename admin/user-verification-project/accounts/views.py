def user_verification(request):
    if request.method == 'POST':
        # Handle user verification logic here
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')  # 'approve' or 'deny'
        
        try:
            user = User.objects.get(id=user_id)
            if action == 'approve':
                user.is_active = True
                user.save()
                messages.success(request, 'User has been approved.')
            elif action == 'deny':
                user.delete()
                messages.success(request, 'User has been denied and removed.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    
    users = User.objects.filter(is_active=False)  # Fetch users pending verification
    return render(request, 'admin/user_verification.html', {'users': users})