from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Client, Mailing


class ClientForm(forms.ModelForm):
    """Форма для создания и редактирования клиентов"""
    
    class Meta:
        model = Client
        fields = ['email', 'full_name', 'phone', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылок"""
    
    class Meta:
        model = Mailing
        fields = ['title', 'subject', 'message', 'clients', 'start_time', 'end_time', 'frequency', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clients'].widget.attrs.update({'class': 'form-control'})
        self.fields['clients'].queryset = Client.objects.all()


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователей"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class MailingFilterForm(forms.Form):
    """Форма фильтрации рассылок"""
    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + Mailing.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    frequency = forms.ChoiceField(
        choices=[('', 'Все частоты')] + Mailing.FREQUENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск по названию...'})
    ) 