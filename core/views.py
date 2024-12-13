from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from core.utils import parse_resume, extract_text_from_pdf
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from .models import JobPosition, JobApplication, CandidateProfile
from .permission import IsCandidate, IsCandidateOrHRManager, IsHRManager
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .serializers import JobApplicationDetailSerializer, JobPositionSerializer, JobApplicationSerializer, RegistrationSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password
import logging
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from .models import CandidateProfile
from .serializers import CandidateProfileSerializer
import openai

openai.api_key = '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'

class IsHRManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_hr_manager

class JobPositionViewSet(viewsets.ModelViewSet):
    queryset = JobPosition.objects.all()
    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated, IsHRManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(hr_manager=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsHRManager])
    def view_candidates(self, request, pk=None):
        # Get the job position instance
        job_position = self.get_object()
        # Get all job applications related to this job position
        job_applications = JobApplication.objects.filter(job_position=job_position)

        job_requirements = job_position.description
        candidates_data = []
        for application in job_applications:
            candidate_profile = application.candidate
            candidates_data.append({
                'candidate_profile': candidate_profile,
                'resume_text': application.parsed_resume,
                'application_id': application.id,
                'match_probability': application.match_probability  # Include existing match_probability
            })

        # Get match probabilities from AI
        ranked_candidates = []
        for data in candidates_data:
            logger.debug(f"Processing JobApplication ID: {application.id}")
            if data['match_probability'] is None:
                logger.debug(f"JobApplication ID {application.id} has no match_probability. Calculating...")
                resume_info = data['resume_text']
                if resume_info:
                    match_prompt = f"""
Given the candidate's information:
{resume_info}

And the job requirements:
{job_requirements}

Rate the candidate's fit for the job as a percentage from 0 to 100.
Please provide only the numeric percentage in your response without the "%". If you ever receive the same informations twice or more give you initial percentage, don't change it
"""

                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an assistant that evaluates candidate resumes based on job requirements and provides a percentage rating only."},
                                {"role": "user", "content": match_prompt}
                            ],
                            max_tokens=10,  # Expecting only a small numeric value
                        )

                        # Extract response text and handle possible formatting
                        response_text = response.choices[0].message['content'].strip()
                        logger.debug(f"AI Response: {response_text}")

                        # Extract the percentage from the response text
                        try:
                            probability = int(response_text)
                            if probability < 0 or probability > 100:
                                probability = 0  # Default to 0 if out of range
                        except ValueError:
                            probability = 0  # Default to 0 if extraction fails

                        # Update the JobApplication instance with the computed match_probability
                        application.match_probability = probability
                        application.save()

                        data['match_probability'] = probability  # Update local data

                    except Exception as e:
                        logger.error(f"Error with OpenAI API: {e}")
                        data['match_probability'] = 0  # Default to 0 in case of error

                else:
                    # If no resume info, assign 0 probability
                    data['match_probability'] = 0
                    application.match_probability = 0
                    application.save()

        # Sort candidates by match probability in descending order
        ranked_candidates = sorted(candidates_data, key=lambda x: x['match_probability'], reverse=True)

        # Prepare response data including application_id
        response_data = [
    {
        'candidate': {
            'username': candidate['candidate_profile'].user.username,
            'first_name': candidate['candidate_profile'].user.first_name,
            'last_name': candidate['candidate_profile'].user.last_name,
            'email': candidate['candidate_profile'].user.email
        },
        'match_probability': f"{candidate['match_probability']}%",
        'application_id': candidate['application_id']
    }
    for candidate in ranked_candidates
]

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def view_resumes(self, request, pk=None):
        # Get the job position instance
        job_position = self.get_object()
        # Get all job applications related to this job position
        job_applications = JobApplication.objects.filter(job_position=job_position)

        # Serialize the job applications
        serializer = JobApplicationSerializer(job_applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_jobs(self, request):
        jobs = JobPosition.objects.all()
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated, IsCandidateOrHRManager]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobApplicationDetailSerializer
        return JobApplicationSerializer

    def create(self, request, *args, **kwargs):
        try:
            candidate_profile = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            raise NotFound("Candidate profile not found for the current user.")

        job_position_id = request.data.get('job_position')
        try:
            job_position = JobPosition.objects.get(id=job_position_id)
        except JobPosition.DoesNotExist:
            raise NotFound("Job position not found.")

        resume = request.FILES.get('resume')  # Make sure we're accessing the uploaded file correctly
        if not resume:
            return Response({"detail": "No resume file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        job_application = JobApplication.objects.create(
            candidate=candidate_profile,
            job_position=job_position,
            resume=resume
        )

        # Extract text using the utility function
        if job_application.resume:
            try:
                resume_text = extract_text_from_pdf(job_application.resume)
                if resume_text.strip():
                    parsed_data = parse_resume(resume_text)
                else:
                    parsed_data = "No text could be extracted from the resume."

                job_application.parsed_resume = parsed_data
                job_application.save()
            except Exception as e:
                print(f"Error processing resume: {e}")
                job_application.parsed_resume = "Parsing failed. Ensure the file is readable and retry."
                job_application.save()

        return Response({"message": "Job application submitted successfully."}, status=status.HTTP_201_CREATED)

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        user = User.objects.filter(username=attrs['username']).first()
        if not user:
            raise serializers.ValidationError("No such user exists.")
        if not user.check_password(attrs['password']):  # Check hashed password
            raise serializers.ValidationError("Incorrect password.")
        return super().validate(attrs)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegistrationView(APIView):
    permission_classes = []  # No authentication required

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create(
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
                email=serializer.validated_data.get('email', ''),
                username=serializer.validated_data['username'],
                password=make_password(serializer.validated_data['password']),
                is_candidate=True  # Automatically set as candidate
            )
            # Create CandidateProfile for the new user
            CandidateProfile.objects.create(user=user)
            return Response({'username': user.username, 'is_candidate': user.is_candidate}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CandidateProfileViewSet(viewsets.ModelViewSet):
    queryset = CandidateProfile.objects.all()
    serializer_class = CandidateProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CandidateProfile.objects.filter(user=self.request.user)
        print("Queryset:", queryset)  # Debug log
        return queryset

    def retrieve(self, request, *args, **kwargs):
        # Retrieve the authenticated user's profile
        candidate_profile = CandidateProfile.objects.filter(user=request.user).first()
        if not candidate_profile:
            return Response({"detail": "Candidate profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(candidate_profile)
        return Response(serializer.data)
    
class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Extract the refresh token from the request
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

    
def home(request):
    return HttpResponse("Backend is working!")
