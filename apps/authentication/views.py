from datetime import datetime, time as datetime_time, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.utils import timezone
from apps.sensors.models import BiomassIndex, Sensor
from apps.devices.models import Device
from .forms import CustomUserCreationForm


def get_demo_plant_photos():
    now = timezone.localtime()
    photo_times = []
    day = now.date()

    while len(photo_times) < 6:
        for hour in (21, 9):
            captured_at = timezone.make_aware(
                datetime.combine(day, datetime_time(hour=hour)),
            )
            if captured_at <= now:
                photo_times.append(captured_at)
        day -= timedelta(days=1)

    return [
        {
            'image': f'sensors/gallery/plant-{index:02}.jpg',
            'captured_at': captured_at,
            'period': 'Вечер' if captured_at.hour == 21 else 'Утро',
        }
        for index, captured_at in enumerate(photo_times[:6], start=1)
    ]


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def dashboard_view(request):
    sensors = Sensor.objects.all()
    devices = Device.objects.all()
    return render(request, 'dashboard.html', {
        'sensors': sensors,
        'devices': devices,
        'biomass_index': BiomassIndex.current().value,
        'gallery_photos': get_demo_plant_photos(),
    })