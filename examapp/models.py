from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator

import random
from django.contrib.auth.models import AbstractUser, BaseUserManager

from django.core.exceptions import ValidationError
from django.db import models

from django.core.mail import send_mail
from datetime import date, timedelta
from django.conf import settings
import phonenumbers
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html
from django.core.validators import FileExtensionValidator
import json  # Import the json module
from django.db.models import Count, F, ExpressionWrapper, FloatField,OuterRef,Subquery
from django.core.mail import send_mail, BadHeaderError
from smtplib import SMTPException  # <- correct source

from django.db.models.functions import Cast

class UserProfileManager(BaseUserManager):
    """Custom manager to allow login with either email or phone."""

    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError("Either an email or phone number is required.")

        email = self.normalize_email(email) if email else None
        phone_number = phone_number if phone_number else None  # Ensure None, not ""

        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, phone_number, password, **extra_fields)


class UserProfile(AbstractUser):

    
    username = None  # Remove default username field
    phone_number = models.CharField(max_length=15,default=None, unique=True, null=True, blank=True)
    ppt_bg_color = models.CharField(max_length=7, default="#ffffff")
    ppt_text_color = models.CharField(max_length=7, default="#000000")
    ppt_highlight_color = models.CharField(max_length=7, default="#00ff00")
    ppt_correct_choice_text = models.CharField(max_length=7, default="#000000")
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'  # Default authentication field
    REQUIRED_FIELDS = ['email']  # Email is optional, but preferred
   
    objects = UserProfileManager()

    def save(self, *args, **kwargs):
        """Normalize phone number before saving to ensure consistency."""
        if self.phone_number:

            # if self.phone_number == '':
            #     self.phone_number = None
            # else:
            self.phone_number = self.normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)


    def clean(self):
        """Ensure phone number is in the correct format before saving."""
        if not self.phone_number:
            raise ValidationError("Telefone irakenewe.")

        if self.phone_number:
            self.phone_number = self.normalize_phone_number(self.phone_number)

            # Validate phone number format
            try:
                parsed_number = phonenumbers.parse(self.phone_number, "RW")
                if not phonenumbers.is_valid_number(parsed_number):
                    raise ValidationError("Telefone nyarwanda yujujwe nabi (+250).")
            except phonenumbers.NumberParseException:
                raise ValidationError("Telefone nyarwanda yujujwe nabi.")

        else:
            self.phone_number = None
    
    def normalize_phone_number(self, phone_number):
        """Ensures phone numbers are always stored in the format: +2507XXXXXXXX."""
        try:
            parsed_number = phonenumbers.parse(phone_number, "RW")
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            return phone_number  # If invalid, return as-is

    

    

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "All Accounts"


    def __str__(self):
        return f"{self.phone_number}"


class SignType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ImagePreviewMixin:
    def image_preview(self, field_name='image', height=100, width=150):
        image = getattr(self, field_name)
        if image:
            return format_html(
                '<img src="{}" style="max-height: {}px; max-width: {}px;" />',
                image.url,
                height,
                width
            )
        return "No Image"
    image_preview.allow_tags = True


class RoadSign(models.Model):
    sign_image = models.ImageField(
    upload_to='road_signs/',
    validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])]
    )
    definition = models.CharField(max_length=100, unique=True)
    type = models.ForeignKey(SignType, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    def image_preview(self):
        """Generates HTML for image preview"""
        if self.sign_image:
            return format_html(
                f'<img src="{self.sign_image.url}" style="max-height: 100px; max-width: 150px;" />'
            )
        return "No Image"

    def __str__(self):
        return self.definition

    @property
    def image_url(self):
        """Returns full URL or None"""
        return self.sign_image.url if self.sign_image else None


class QuestionManager(models.Manager):
    def get_questions_with_index(self):
        return [(index + 1, question) for index, question in enumerate(self.all())]


class Question(models.Model):
    QUESTION_CHOICES = [(i, f"Choice {i}") for i in range(1, 5)]

    question_text = models.TextField(verbose_name="Question Text")
    question_type = models.ForeignKey('ExamType', on_delete=models.SET_NULL, null=True, verbose_name="Question Type")

    question_sign = models.ForeignKey(
        'RoadSign', related_name='questions', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Question Image"
    )

    # Choices as separate fields
    choice1_text = models.CharField(max_length=700, blank=True, verbose_name="Choice 1 Text")
    choice2_text = models.CharField(max_length=500, blank=True, verbose_name="Choice 2 Text")
    choice3_text = models.CharField(max_length=255, blank=True, verbose_name="Choice 3 Text")
    choice4_text = models.CharField(max_length=255, blank=True, verbose_name="Choice 4 Text")

    # Choices as related RoadSigns
    choice1_sign = models.ForeignKey(
        'RoadSign', blank=True, null=True, verbose_name="Choice 1 Sign",
        related_name="choice1_questions", on_delete=models.SET_NULL
    )
    choice2_sign = models.ForeignKey(
        'RoadSign', blank=True, null=True, verbose_name="Choice 2 Sign",
        related_name="choice2_questions", on_delete=models.SET_NULL
    )
    choice3_sign = models.ForeignKey(
        'RoadSign', blank=True, null=True, verbose_name="Choice 3 Sign",
        related_name="choice3_questions", on_delete=models.SET_NULL
    )
    choice4_sign = models.ForeignKey(
        'RoadSign', blank=True, null=True, verbose_name="Choice 4 Sign",
        related_name="choice4_questions", on_delete=models.SET_NULL
    )

    correct_choice = models.PositiveSmallIntegerField(
        choices=QUESTION_CHOICES, verbose_name="Correct Choice Number"
    )
    order = models.PositiveIntegerField(default=1, verbose_name="Display Order", unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def get_choices(self):
        choices = []
        for i in range(1, 5):
            text = getattr(self, f'choice{i}_text')
            sign = getattr(self, f'choice{i}_sign')

            if text:
                choices.append({
                    'id': i,  # Add the choice ID
                    'type': 'text',
                    'content': text,
                    'is_correct': i == self.correct_choice
                })
            elif sign:
                choices.append({
                    'id': i,  # Add the choice ID
                    'type': 'image',
                    'content': sign.image_url if sign else None,
                    'is_correct': i == self.correct_choice
                })
        return choices

    def __str__(self):
        return f"Q{self.order}: {self.question_text}... [type: {self.question_type.name if self.question_type else 'None'}]"

class ExamType(models.Model):
    name = models.CharField(max_length=500, default='Ibivanze')
    order = models.IntegerField(default=5)


    def __str__(self):
        return self.name

class Exam(models.Model):
    timezone = timezone.localtime(timezone.now()).strftime('%d.%m.%Y %H')

    exam_type = models.ForeignKey(ExamType, on_delete=models.SET_NULL, null=True, blank=True )

    schedule_hour = models.TimeField(null=True, blank=True, help_text="Hour when the exam should be published")
    questions = models.ManyToManyField(Question, related_name='exams')
    duration = models.PositiveIntegerField(default=20,help_text="Duration of the exam in minutes")
    for_scheduling = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        now = timezone.localtime(timezone.now())
        if not self.pk and not self.created_at:
            self.created_at = now
        self.updated_at = now
        super().save(*args, **kwargs)
    

    is_active = models.BooleanField(default=False)


    class Meta:
        ordering = ['-created_at']
        verbose_name = "Exam"
        verbose_name_plural = "All Exams"



    @property
    def total_questions(self):
        return self.questions.count()

    @property
    def total_score(self):
        return self.total_questions

    # def remaining_attempts(self, user):
    #     attempts = UserExam.objects.filter(user=user, exam=self).count()
    #     return self.max_attempts - attempts

    def __str__(self):
        return f"{self.schedule_hour.strftime('%H:%M') if self.schedule_hour else 'No Hour'} / {self.updated_at.strftime('%d.%m.%Y')} - {self.exam_type.name if self.exam_type else 'None'}"

