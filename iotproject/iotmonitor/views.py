import csv

from awesome_django_timezones.middleware import TimezonesMiddleware
from django.contrib.auth import authenticate
from django.db.models import Count
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import decorator_from_middleware
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import connection
import json

from .models import Thing, TypeOfThing, Sensor

def lista_produtos(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from produtos")
        row = cursor.fetchall()
        return HttpResponse(row)

def entrada_estoque(request, pk):
    with connection.cursor() as cursor:
        cursor.execute("update produtos set estoque=estoque+1 where id=%s", [pk])
        cursor.execute("SELECT * from produtos where id = %s", [pk])
        row = cursor.fetchone()
        return HttpResponse(row)

def saida_estoque(request, pk):
    with connection.cursor() as cursor:
        cursor.execute("update produtos set estoque=estoque-1 where id=%s and estoque>=0", [pk])
        cursor.execute("SELECT * from produtos where id = %s", [pk])
        row = cursor.fetchone()
        return HttpResponse(row)

@require_POST
def cadastro_produto(request):
    with connection.cursor() as cursor: 
        corpo = json.loads(request.body)
        descricao = corpo['descricao']
        tamanho = corpo['tamanho']
        estoque = corpo['estoque']
        codigo = corpo['codigo']
        preco_compra = corpo['preco_compra']
        preco_venda = corpo['preco_venda']
        cursor.execute("insert into produtos (descricao, tamanho, estoque, codigo, preco_compra, preco_venda)\
        values (%s, %s, %s, %s, %s, %s)", [descricao, tamanho, estoque, codigo, preco_compra, preco_venda])
        row = cursor.lastrowid
        return HttpResponse(row)

def thing_list(request):
    types = TypeOfThing.objects.all().order_by('name').annotate(things_count=Count('thing'))
    things_without_type = Thing.objects.filter(type_of_thing__isnull=True)
    return render(request, 'iotmonitor/thing_list.html',
                  {'types': types, 'things_without_type': things_without_type})

timezone_decorator = decorator_from_middleware(TimezonesMiddleware)

@timezone_decorator
def thing_detail(request, pk):
    thing = Thing.objects.get(pk=pk)
    sensors = thing.sensor_set.all().order_by('name')
    return render(request, 'iotmonitor/thing_detail.html',
                  {'thing': thing, 'sensors': sensors})


# use the csrf_exempt tag since this view will be accessed from a external device
@csrf_exempt
@require_POST
def new_reading(request):
    # use POST parameters to authenticate
    user = authenticate(username=request.POST.get('sensor'), password=request.POST.get('password'))
    if user is not None:
        try:
            user.sensor.reading_set.create(value=float(request.POST.get('value')))
            user.sensor.save()
            return HttpResponse('Sensor authenticated and data succesfully recorded.')

        except:
            return HttpResponseBadRequest(
                'Sensor authenticated but unable to record data. Make sure your sensor provided a value that can be parsed onto a numerical value.')
    else:
        response = HttpResponseForbidden(
            'Sensor not authenticated. Please check its username ({}) and password.'.format(request.POST.get('sensor')))
        return response

def export_readings_csv(request, pk):
    sensor = Sensor.objects.get(pk=pk)
    thing_name = sensor.thing_monitored.name
    readings = sensor.reading_set.all().values_list('created_date', 'value')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="readings_{}_{}.csv"'.format(thing_name, sensor.name)

    writer = csv.writer(response)
    writer.writerow(['Thing', 'Sensor', 'Date', 'Time', 'Timezone', 'Value'])

    for reading in readings:
        reading_local_datetime = timezone.localtime(reading[0])
        row = [
            thing_name,
            sensor.name,
            reading_local_datetime.date(),
            reading_local_datetime.strftime('%H:%M:%S'),
            reading_local_datetime.strftime('%z'),
            reading[1]]
        writer.writerow(row)

    return response
