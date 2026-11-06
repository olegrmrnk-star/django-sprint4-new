from django.utils import timezone
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.core.paginator import Paginator

from .models import Category, Post, Comment
from .forms import ProfileEditForm, PostForm, CommentForm


def get_published_posts(category=None):
    """
    Возвращает QuerySet опубликованных постов.
    Если передан category, то фильтрует только по этой категории.
    """
    queryset = Post.objects.all()

    base_filters = {
        'is_published': True,
        'pub_date__lte': timezone.now().date(),
        'category__isnull': False,
        'category__is_published': True,
    }
    # Если нужна конкретная категория, добавляем её к фильтрам
    if category is not None:
        base_filters['category'] = category

    return queryset.filter(**base_filters)


def get_paginated_context(object_list, request, per_page=10):
    paginator = Paginator(object_list, per_page)
    page_number = request.GET.get('page')
    pg_obj = paginator.get_page(page_number)
    return pg_obj


def index(request):
    template = 'blog/index.html'
    post_list = get_published_posts()
    post_list = post_list.annotate(comment_count=Count('comments'))
    post_list = post_list.select_related(
        'category',
    ).order_by('-pub_date')
    page_obj = get_paginated_context(post_list, request)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(Post, id=post_id,)
    if request.user != post.author:
        is_ready = (
            post.is_published and post.pub_date <= timezone.now()
            and post.category and post.category.is_published
        )
        if not is_ready:
            raise Http404
    form = CommentForm() if request.user.is_authenticated else None
    comments = post.comments.all().order_by('created_at')
    context = {'post': post, 'form': form, 'comments': comments}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    posts = get_published_posts(
        category=category
    ).order_by('-pub_date')
    posts = posts.annotate(comment_count=Count('comments'))
    page_obj = get_paginated_context(posts, request)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template, context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    template = 'blog/create.html'
    context = {'form': form}
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    user_obj = get_object_or_404(User, username=username)
    if request.user == user_obj:
        posts = user_obj.posts.all()
    else:
        posts = get_published_posts().filter(author=user_obj)
    posts = posts.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    page_obj = get_paginated_context(posts, request)
    context = {'profile': user_obj, 'page_obj': page_obj}
    return render(request, template, context)


@login_required
def edit_profile(request):
    form = ProfileEditForm(instance=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    template = 'blog/user.html'
    context = {'form': form}
    return render(request, template, context)


def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    template = 'blog/create.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'GET':
        form = PostForm(instance=post)
        return render(request,
                      'blog/create.html',
                      {'form': form, 'post': post}
                      )
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm()
    return render(
        request,
        'blog/detail.html',
        {'form': form, 'post': post, 'comments': post.comments.all()}
    )


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
        'post': post
    })


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post.id)
    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post': post
    })
