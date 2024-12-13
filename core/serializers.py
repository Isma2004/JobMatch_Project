# core/serializers.py
from rest_framework import serializers
from .models import JobPosition, JobApplication, User, CandidateProfile

class JobPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosition
        fields = ['id', 'title', 'description', 'requirements', 'hr_manager']
        read_only_fields = ['hr_manager']


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = '__all__'
        read_only_fields = ['match_probability']  # Make match_probability read-only

class JobApplicationDetailSerializer(serializers.ModelSerializer):
    candidate_username = serializers.CharField(source='candidate.user.username', read_only=True)
    candidate_first_name = serializers.CharField(source='candidate.user.first_name', read_only=True)
    candidate_last_name = serializers.CharField(source='candidate.user.last_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.user.email', read_only=True)
    match_probability = serializers.IntegerField(read_only=True)  # Included new field

    class Meta:
        model = JobApplication
        fields = ['id', 'resume', 'parsed_resume', 'job_position', 'candidate',
                  'candidate_username', 'candidate_first_name', 'candidate_last_name', 'candidate_email', 'match_probability']

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def create(self, validated_data):
        # Automatically set is_candidate to True and is_hr_manager to False
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            is_candidate=True,  # Always set as candidate
            is_hr_manager=False  # Prevent HR registration
        )
        return user
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class CandidateProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nested serializer to include user details
    class Meta:
        model = CandidateProfile
        fields = ['id', 'username', 'first_name', 'last_name', 'email']