from django.db import models

# Create your models here.
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser

# User model for candidates and HR managers
class User(AbstractUser):
    # Extending the default User model to include roles for candidate and HR manager
    is_candidate = models.BooleanField(default=False)
    is_hr_manager = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True)

    # Override save method to auto-generate the slug from the username
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.username)
        super().save(*args, **kwargs)

# Candidate profile model
class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile")
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)

    def __str__(self):
        return self.user.username

# Job position model
class JobPosition(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    hr_manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_positions', null=True, blank=True)


# Job application model
class JobApplication(models.Model):
    job_position = models.ForeignKey(JobPosition, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(upload_to='job_applications/', null=True, blank=True)  # Ensure this field is present
    parsed_resume = models.TextField(null=True, blank=True)  # Store parsed resume content
    match_probability = models.IntegerField(null=True, blank=True)  # New field added