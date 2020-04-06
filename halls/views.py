from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views import generic
from django.contrib.auth import authenticate, login
from .models import Hall, Video
from .forms import Videoform, Searchform
from django.forms.utils import ErrorList
import requests
import urllib

YOUTUBE_API_KEY = 'AIzaSyDXHhR5KqhV2YgDnnMBwI2Nw-ZyWpRhU7I'


def home(request):
    recent_halls = Hall.objects.all().order_by('-id')[:3]
    popular_halls = [Hall.objects.get(pk=1), Hall.objects.get(pk=2), Hall.objects.get(pk=3)]
    return render(request, 'halls/home.html', {'recent': recent_halls, 'popular': popular_halls})


def dashboard(request):
    halls = Hall.objects.filter(user=request.user)
    return render(request, 'halls/dashboard.html', {'halls': halls})


def add_video(request, pk):
    form = Videoform()
    search_form = Searchform()
    hall = Hall.objects.get(pk=pk)

    if not hall.user == request.user:
        raise Http404
    if request.method == "POST":
        form = Videoform(request.POST)
        if form.is_valid():
            video = Video()
            video.hall = hall
            video.url = form.cleaned_data['url']
            parsed_url = urllib.parse.urlparse(video.url)
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v')
            if video_id:
                video.youtube_id = video_id[0]
                response = requests.get(
                    f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id[0]}&key={YOUTUBE_API_KEY}')
                json = response.json()
                title = json['items'][0]['snippet']['title']
                video.title = title
                video.save()
                return redirect('detail_hall', pk)
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('Needs to be a YouTube URL')
    return render(request, 'halls/add_video.html', {'form': form, 'search_form': search_form, 'hall': hall})


def video_search(request):
    search_form = Searchform(request.GET)
    if search_form.is_valid():
        encoded_search_term = urllib.parse.quote(search_form.cleaned_data['search_term'])
        response = requests.get(
            f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q={encoded_search_term}&key={YOUTUBE_API_KEY}')
        return JsonResponse(response.json())
    return JsonResponse({'error': 'Not able to validate form'})


class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('dashboard')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return view


class CreateHall(generic.CreateView):
    model = Hall
    fields = ['title']
    template_name = 'halls/create_hall.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        super(CreateHall, self).form_valid(form)
        return redirect('dashboard')


class DetailHall(generic.DetailView):
    model = Hall
    template_name = 'halls/detail_hall.html'


class UpdateHall(generic.UpdateView):
    model = Hall
    template_name = 'halls/update_hall.html'
    fields = ['title']
    success_url = reverse_lazy('dashboard')


class DeleteHall(generic.DeleteView):
    model = Hall
    template_name = 'halls/delete_hall.html'
    success_url = reverse_lazy('dashboard')


class DeleteVideo(generic.DeleteView):
    model = Video
    template_name = 'halls/delete_video.html'
    success_url = reverse_lazy('dashboard')
