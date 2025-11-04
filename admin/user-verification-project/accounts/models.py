class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    identification_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class VerificationRequest(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Verification request for {self.user_profile.user.username}"