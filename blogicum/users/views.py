from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import Profile
from .forms import CustomUserCreationForm, ProfileForm


@login_required
def profile_view(request):
    profile = request.user.profile
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'blog/profile.html', context)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:index')
    else:
        form = CustomUserCreationForm()
    return render(
        request,
        'registration/registration_form.html',
        {'form': form}
    )
