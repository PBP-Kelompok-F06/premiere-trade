from django.shortcuts import render

# Create your views here.
def show_main(request):
    context = {
        'meong' : 'meong'
    }

    return render(request, "main.html", context)