import datetime
from .models import Pemain
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse
from django.core import serializers
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@login_required(login_url='/login')
def menampilkan_list_pemain_yang_sedang_dijual(request):
    pemain_list = Pemain.objects.filter(sedang_dijual = True)

    context = {
        'pemain_list': pemain_list,
    }

    return render(request, "list_pemain_dijual.html", context)

























def show_xml(request):
     pemain_list = Pemain.objects.all()
     xml_data = serializers.serialize("xml", pemain_list)
     return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    pemain_list = Pemain.objects.select_related('user').all()
    
    data = [
        {
            'id': str(pemain.id),
            'nama_pemain': pemain.nama_pemain,
            'club': pemain.club,
            'umur': pemain.umur,
            'market_value': pemain.market_value,
            'negara': pemain.negara,
            'jumlah_goal': pemain.jumlah_goal,
            'jumlah_asis': pemain.jumlah_asis,
            'jumlah_match': pemain.jumlah_match,
            'sedang_dijual': pemain.sedang_dijual,
            'user_id': pemain.user.id if pemain.user else None,
        }
        for pemain in pemain_list
    ]

    return JsonResponse(data, safe=False)


def show_xml_by_id(request, product_id):
   try:
       product_item = Pemain.objects.filter(pk=product_id)
       xml_data = serializers.serialize("xml", product_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Pemain.DoesNotExist:
       return HttpResponse(status=404)

def show_json_by_id(request, product_id):
    try:
        pemain = Pemain.objects.select_related('user').get(pk=product_id)
        data = {
            'id': str(pemain.id),
            'nama_pemain': pemain.nama_pemain,
            'club': pemain.club,
            'umur': pemain.umur,
            'market_value': pemain.market_value,
            'negara': pemain.negara,
            'jumlah_goal': pemain.jumlah_goal,
            'jumlah_asis': pemain.jumlah_asis,
            'jumlah_match': pemain.jumlah_match,
            'sedang_dijual': pemain.sedang_dijual,
            'user_username': pemain.user.username if pemain.user else 'Anonymous'
        }
        return JsonResponse(data)
    except Pemain.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)