from django import forms
from django.contrib.auth.models import User

from core.constants import MODERATION_ERROR
from .models import Comment, Post
from .moderation import is_toxic


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title',
            'text',
            'pub_date',
            'category',
            'location',
            'image',
        ]
        image = forms.ImageField(required=False, widget=forms.FileInput)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']  # Только текст комментария
        labels = {'text': 'Ваш комментарий'}
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if is_toxic(text):
            raise forms.ValidationError(MODERATION_ERROR)
        return text
