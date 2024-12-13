from django.contrib import admin
from .models import User, CandidateProfile, JobPosition, JobApplication

# Register the custom User model with the admin
admin.site.register(User)

# Register the CandidateProfile, JobPosition, and JobApplication models
admin.site.register(CandidateProfile)
admin.site.register(JobPosition)
admin.site.register(JobApplication)
# Register your models here.
