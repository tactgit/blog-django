#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404
from django.views.generic import View
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

import markdown2

from . import models, forms

# Create your views here.

class Index(View):
    template_name = 'main/index.html'
    def get(self, request):
        data = {}
        posts = models.Post.objects.filter(is_draft=False).order_by('-id')
        pages = models.Page.objects.all()
        data['posts'] = posts
        data['pages'] = pages
        return render(request, self.template_name, data)

class Post(View):
    template_name = 'main/post.html'
    def get(self, request, pk):
        try:
            pk = int(pk)
            post = models.Post.objects.get(pk=pk)
        except models.Post.DoesNotExist:
            raise Http404
        data = {'post':post}
        return render(request, self.template_name, data)

class Page(View):
    template_name = 'main/page.html'
    def get(self, request, pk):
        try:
            pk = int(pk)
            page = models.Page.objects.get(pk=pk)
        except page.DoesNotExist:
            raise Http404
        data = {'page':page}
        return render(request, self.template_name, data)

class AdminIndex(View):
    template_name = 'blog_admin/index.html'
    @method_decorator(login_required)
    def get(self, request):
        data = {}
        return render(request, self.template_name, data)

class AdminPosts(View):
    template_name = 'blog_admin/posts.html'

    @method_decorator(login_required)
    def get(self, request):
        data = {}
        draft = request.GET.get('draft')
        if draft and draft.lower()=='true':
            flag = True
        else:
            flag = False
        # posts = models.Post.objects.filter(is_draft=flag).order_by('-update_time')
        posts = models.Post.objects.filter(is_draft=flag)
        posts = posts.order_by('-update_time')
        data['posts'] = posts
        return render(request, self.template_name, data)

class AdminPost(View):
    template_name = 'blog_admin/post.html'

    @method_decorator(login_required)
    def get(self, request, pk=0, form=None):
        data = {}
        form_data = {}
        if pk:
            try:
                pk = int(pk)
                post = models.Post.objects.get(pk=pk)
                form_data['title'] = post.title
                form_data['content'] = post.raw
                form_data['abstract'] = post.abstract
                data['edit_flag'] = True
            except models.Post.DoesNotExist:
                raise Http404
        if not form:
            form = forms.NewPost(initial=form_data)
        data['form'] = form
        return render(request, self.template_name, data)

    @method_decorator(login_required)
    def post(self, request, pk=0, form=None):
        form = forms.NewPost(request.POST)
        if form.is_valid():
            if not pk:
                cur_post = models.Post()
            else:
                try:
                    pk = int(pk)
                    cur_post = models.Post.objects.get(pk=pk)
                except models.Post.DoesNotExist:
                    raise Http404
            cur_post.title = form.cleaned_data['title']
            cur_post.raw = form.cleaned_data['content']
            cur_post.abstract = form.cleaned_data['abstract']
            html = markdown2.markdown(cur_post.raw, extras=['code-friendly', 'fenced-code-blocks'])
            cur_post.content_html = html
            cur_post.author = request.user
            if request.POST.get('publish'):
                cur_post.is_draft = False
                cur_post.save()
                # return HttpResponse('Post has been pulished!')
                # return redirect('/admin/posts')
                # return redirect(reverse('main:admin_edit_post', kwargs={'pk':cur_post.id}))
                msg = 'Post has been pulished!'
                messages.add_message(request, messages.SUCCESS, msg)
                return redirect(reverse('main:admin_posts'))
            else:
                cur_post.is_draft=True
                cur_post.save()
                msg = 'Draft has been saved!'
                messages.add_message(request, messages.SUCCESS, msg)
                url = '{0}?draft=true'.format(reverse('main:admin_posts'))
                return redirect(url)

        return self.get(request, form)

class DeletePost(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        try:
            pk = int(pk)
            cur_post = models.Post.objects.get(pk=pk)
            is_draft = cur_post.is_draft
            url = reverse('main:admin_posts')
            if is_draft:
                url = '{0}?draft=true'.format(url)    
            cur_post.delete()
        except models.Post.DoesNotExist:
            raise Http404

        return redirect(url)

        
class AdminTags(View):
    template_name = 'blog_admin/tags.html'

    @method_decorator(login_required)
    def get(self, request):
        tags = models.Tag.objects.all()
        data = {'tags':tags}

        return render(request, self.template_name, data)

class AdminFilterPosts(View):
    template_name = 'blog_admin/posts.html'

    @method_decorator(login_required)
    def get(self, request):
        tag_id = request.GET.get('tag')
        catagory_id = request.GET.get('catagory')

        if tag_id:
            posts = filter_posts_by_tag(tag_id)
        elif catagory_id:
            posts = filter_posts_by_catagory(catagory_id)
        else:
            url = reverse('main:admin_posts')
            return redirect(url)

        if posts == None:
            raise Http404

        data = {'posts':posts}
        return render(request, self.template_name, data)

def filter_posts_by_tag(pk):
    try:
        tag = models.Tag.objects.get(pk=pk)
    except models.Tag.DoesNotExist:
        return None

    posts = tag.post_set.all()
    return posts

def filter_posts_by_catagory(pk):
    try:
        catagory = models.Catagory.objects.get(pk=pk)
    except models.Catagory.DoesNotExist:
        return None

    posts = catagory.post_set.all()
    return posts

