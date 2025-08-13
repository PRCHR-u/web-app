from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy # Used for redirecting after successful registration

from django.contrib.auth.decorators import login_required
from users.forms import CustomUserForm # Import the custom user form
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page - login page for example
            # Ensure you have a URL named 'login' in your project's URLs
            return redirect(reverse_lazy('login'))
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    # The logged-in user is available as request.user
    user = request.user
    return render(request, 'users/profile.html', {'user': user})

@login_required # Decorator to ensure user is logged in
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            # Redirect to the profile page after successful update
            return redirect(reverse_lazy('profile'))
    else:
        form = CustomUserForm(instance=request.user) # Pre-populate form with current user data
    return render(request, 'users/edit_profile.html', {'form': form})
    