from .utils import paginate_page
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie


@cache_page(20, key_prefix='index_page')
@vary_on_cookie
def index(request):
    template = 'posts/index.html'

    post_list = Post.objects.select_related("group", "author")
    page_obj = paginate_page(request, post_list)
    context = {'page_obj': page_obj,
               'post_list': post_list}
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts_in_group.all()
    page_obj = paginate_page(request, post_list)
    context = {'group': group,
               'page_obj': page_obj,
               }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    author = get_object_or_404(User, username=username)
    post_list = author.posts_of_author.all()
    page_obj = paginate_page(request, post_list)
    # is_profile used in template /includes/article.html
    # it deactivetes author name in articles
    # if they are renderd on profile page
    context = {'author': author,
               'page_obj': page_obj,
               'is_profile': True,
               }

    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    context['following'] = following
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    form = CommentForm()

    post = get_object_or_404(Post, pk=post_id)
    context = {'post': post,
               'form': form,
               'comments': post.comments_to_post.all()
               }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    context = {
        'form': form,
        'is_edit': False
    }

    if not request.POST:
        return render(request, template, context)

    if not form.is_valid():
        return render(request, template, context)

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(reverse_lazy('posts:profile', args=[request.user]))


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'

    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect(reverse_lazy('posts:post_detail', args=[post_id]))

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)

    if form.is_valid():
        form.save()
        return redirect(reverse_lazy('posts:post_detail', args=[post_id]))

    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, template, context)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, post_list)
    context = {'page_obj': page_obj, }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    flw_inst = Follow.objects.filter(
        user=request.user,
        author=author)
    if flw_inst.exists():
        flw_inst.delete()
    return redirect('posts:profile', username=username)
