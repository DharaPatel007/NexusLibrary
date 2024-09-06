# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# from django.core.exceptions import ValidationError

# class CustomSignupForm(UserCreationForm):
#     email = forms.EmailField(required=True, help_text="Enter a valid email address.")

#     class Meta:
#         model = User
#         fields = ('username', 'email', 'password1', 'password2')

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if User.objects.filter(email=email).exists():
#             raise ValidationError("This email address is already in use.")
#         return email

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         if User.objects.filter(username=username).exists():
#             raise ValidationError("This username is already taken.")
#         return username

#     def clean_password2(self):
#         password1 = self.cleaned_data.get('password1')
#         password2 = self.cleaned_data.get('password2')
#         if password1 and password2 and password1 != password2:
#             raise ValidationError("Passwords do not match.")
#         return password2
    
    
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from library.models import StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile

class CustomSignupForm(UserCreationForm):
    USER_TYPES = (
        ('Student', 'Student'),
        ('Researcher', 'Researcher'),
        ('Faculty', 'Faculty'),
        ('Guest', 'Guest'),
    )
    user_type = forms.ChoiceField(choices=USER_TYPES, label="User Type")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type')

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data['user_type']

        if commit:
            user.save()
            # Create the appropriate profile based on user_type
            profile_classes = {
                'Student': StudentProfile,
                'Researcher': ResearcherProfile,
                'Faculty': FacultyProfile,
                'Guest': GuestProfile,
            }
            profile_class = profile_classes.get(user_type, StudentProfile)  # Default to StudentProfile if invalid
            profile_class.objects.create(user=user, user_type=user_type)
        return user