from itertools import chain
from .forms import CommentForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount, Comment
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from uuid import UUID
import uuid

import random


# Create your views here.


@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    user_following_list = []
    feed = []

    user_following = FollowersCount.objects.filter(follower=request.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    # user suggestion starts
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)

    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    sugg_username_profile_list = list(chain(*username_profile_list))

    return render(request, 'index.html', {'user_profile': user_profile, 'posts': feed_list,
                                          'sugg_username_profile_list': sugg_username_profile_list[:4]})


def post_detail(request, id):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    post = get_object_or_404(Post, id=id)
    comments = post.comment_set.all()
    context = {
        'post': post,
        'comments': comments,
        'user_profile': user_profile
    }
    return render(request, 'post_detail.html', context)


def add_comment_to_post(request, id):
    post = get_object_or_404(Post, id=id)
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect('index')
    else:
        form = CommentForm()

    return render(request, 'add_comment_to_post.html', {
        'form': form,
        'user_profile': user_profile
    })


def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        passwordtwo = request.POST['passwordtwo']
        if password == passwordtwo:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'The email is already used')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'The username has already exists!')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password is not matching')
            return redirect('signup')
    else:
        return render(request, 'signup1.html')


@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/' + user)
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/' + user)
    else:
        return redirect('/')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Login or Password is invalid')
            return redirect('signin')

    return render(request, 'signin1.html')


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        about = request.POST['about']
        location = request.POST['location']
        if request.FILES.get('img') is None:
            user_profile.bio = about
            user_profile.location = location
            user_profile.save()
            messages.info(request, 'Profile has been updated successfully!')
        elif request.FILES.get('img') is not None:
            profile_img = request.FILES.get('img')
            user_profile.profileImg = profile_img
            user_profile.bio = about
            user_profile.location = location
            user_profile.save()
            messages.info(request, 'Profile has been updated successfully!')
        return redirect('index')
    return render(request, 'setting.html', {'user_profile': user_profile})


def upload(request):
    if request.method == 'POST':
        user_objects = request.user.username
        user_image = request.FILES.get('image_upload')
        user_caption = request.POST['caption']
        user_post = Post.objects.create(user=user_objects, image=user_image, caption=user_caption)
        user_post.save()
        return redirect('/')
    else:
        return redirect('')
    return HttpResponse('<h1>Upload view</h1>')


@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')
    post = Post.objects.get(id=post_id)
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    if like_filter is None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.number_of_likes += 1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.number_of_likes -= 1
        post.save()
        return redirect('/')


def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)

    follower = request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(request, 'profile.html', context)


def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    username_profile = []
    username_profile_list = []
    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html',
                  {'user_profile': user_profile, 'username_profile_list': username_profile_list, 'search': username})


# def update_post(request, post_id):
#     if request.method == 'POST':
#         # Retrieve the post to be updated
#         try:
#             post = Post.objects.get(id=post_id, user=request.user)
#         except Post.DoesNotExist:
#             # Post not found or user doesn't own the post
#             return redirect('index')  # Or any appropriate URL
#
#         # Process the updated post data
#         # Example: updating the post's content
#         post.content = request.POST.get('content')
#         post.save()
#
#         return redirect('index')  # Or any appropriate URL
#
#     # If the request is not a POST request, render the update post form
#     try:
#         post = Post.objects.get(id=post_id, user=request.user)
#     except Post.DoesNotExist:
#         # Post not found or user doesn't own the post
#         return redirect('index')  # Or any appropriate URL
#
#     context = {
#         'post': post,
#     }
#     return render(request, 'update_post.html', context)

def delete_post(request, post_id):
    if request.method == 'POST':
        # Retrieve the post to be deleted
        try:
            post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            # Post not found or user doesn't own the post
            return redirect('index')  # Or any appropriate URL

        # Delete the post
        post.delete()

        return redirect('index')  # Or any appropriate URL

    # If the request is not a POST request, render the delete post confirmation page
    try:
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        # Post not found or user doesn't own the post
        return redirect('index')  # Or any appropriate URL

    context = {
        'post': post,
    }
    return render(request, 'delete_post.html', context)
