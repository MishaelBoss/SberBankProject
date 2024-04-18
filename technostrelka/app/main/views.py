from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.mail import send_mail
from .models import *
from django.conf import settings
from threading import Thread
from datetime import date
import os

email_server = settings.EMAIL_HOST_USER


def is_email(data):
    try:
        validate_email(data)
    except:
        return False
    else:
        return True


def rassylka(subject, text, emails):
    send_mail(subject, text, email_server, emails, fail_silently=False)

def index(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    query = str(request.GET.get('query', ''))
    if query is None:
        all_events = list(Event.objects.all().order_by('-id').all())
    else:
        all_events = []
        for i in list(Event.objects.all().order_by('-id')):
            if query.lower() in i.name.lower() or i.name.lower() in query.lower():
                all_events.append(i)
    events = []
    for i in all_events:
        if not i.can_add_balls():
            events.append(i)
    i_participate = []
    delta_s = []
    delta_ss = []
    for event in events:
        if EventMember.objects.filter(user=_login, event_id=event.id).first() is None:
            i_participate.append(False)
        else:
            i_participate.append(True)

        delta_s.append((event.to_date-date.today()).days)
        delta_ss.append((event.from_date-date.today()).days)

    if query is None or query == 'None':
        query  = ''
    context = {
        'events': list(zip(events, i_participate, delta_s, delta_ss)),
        'query': query
    }
    return render(request, 'index.html', context=context)


def login_page(request):
    if request.method == "POST":
        _login = request.POST['login']
        password = request.POST['password']
        if is_email(_login):
            user = User.objects.filter(email=_login).first()
            _login = user.username
            user = authenticate(request, username=_login, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                return redirect('/login')
        else:
            user = authenticate(request, username=_login, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                return redirect('/login')
    else:
        return render(request, 'login.html')
    

def register_page(request):
    if request.method == "POST":
        _login = request.POST['login']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.create_user(_login, email, password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            user = authenticate(request, username=_login, password=password)
            ub = UserBalance(user=_login)
            
            login(request, user)
            thread = Thread(target=send_mail,
                                         args=("Регистрация", f"Здравствуйте, {last_name} {first_name}, Вы успешно зарегистрировались на SberEvent!", email_server, [email]))
            thread.start()
            ub.save()
            
            return redirect('/')
        except Exception as ex:
            print(ex)
            return redirect('/register')
    else:
        return render(request, 'register.html')
    

def logout_page(request):
    logout(request)
    return redirect('/login')


def add_event(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    if request.POST:
        try:
            name = request.POST['name']
            description = request.POST['description']
            is_public = request.POST['is_public'] == 'public'
            from_date = request.POST['from_date']
            to_date = request.POST['to_date']
            balance = int(request.POST['balance'])
            places = int(request.POST['places'])
            image = request.FILES['image']

            event_obj = Event(author=_login, name=name, is_public=is_public, description=description, from_date=from_date, to_date=to_date, balance=balance, image=image, places=places)
            event_obj.save()
            return redirect('/')
        except Exception as ex:
            print(ex)
            return redirect('/add_event')
    else:
        return render(request, 'add_event.html')
    

def participate(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    event_id = int(request.GET['event_id'])
    event = Event.objects.filter(id=event_id).first()
    if event.places > 0:
        event.places -= 1
        event.save()
        em = EventMember(event_id=event_id, user=_login)
        em.save()
        thread = Thread(target=send_mail,
                                         args=("Регистрация", f"Здравствуйте! Вы успешно зарегистрировались на {event.name}!", email_server, [User.objects.filter(username=_login).first().email]))
        thread.start()
    return redirect('/')


def unparticipate(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    event_id = int(request.GET['event_id'])
    event = Event.objects.filter(id=event_id).first()
    if (event.from_date-date.today()).days > 1:
        event.places += 1
        event.save()
        em = EventMember.objects.filter(event_id=event_id, user=_login).first()
        if em is not None:
            em.delete()
            thread = Thread(target=send_mail,
                                         args=("Отмена", f"Здравствуйте! Вы успешно отменили запланированное мероприятие {event.name}!", email_server, [User.objects.filter(username=_login).first().email]))
            thread.start()
    return redirect('/')


def myevents(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    
    events = Event.objects.filter(author=_login).order_by('-id').all()

    can_add_balls = []

    for event in events:
        can_add_balls.append((date.today() - event.to_date).days > 0)

    context = {
        'events': list(zip(events, can_add_balls))
    }
    return render(request, 'myevents.html', context=context)


def view_event(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    event_id = int(request.GET['event_id'])

    event = Event.objects.filter(id=event_id).first()
    email = User.objects.filter(username=event.author).first().email

    context = {
        'event': event,
        'email': email
    }


    return render(request, 'view.html', context=context)


def get_participats(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    event_id = int(request.GET['event_id'])
    users = []
    em = EventMember.objects.filter(event_id=event_id).all()
    for i in em:
        users.append(User.objects.filter(username=i.user).first())

    context = {
        'users': users
    }

    return render(request, 'get_participats.html', context=context)


def change_data(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if request.POST:
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        if old_password != '' and new_password != '':
            if not user.check_password(old_password):
                return redirect('/change_data')
            if (old_password == '' and new_password != '') or (old_password != '' and new_password == ''):
                return redirect('/change_data')
            user.set_password(new_password)
        user.save()
        login(request, user)
        return redirect('/')
    else:
        context = {
            'user': user
        }
        return render(request, 'change_data.html', context=context)
    

def edit_event(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    event_id = int(request.GET['event_id'])

    event = Event.objects.filter(id=event_id).first()
    if event.author != _login:
        return redirect('/login')
    
    if request.POST:
        try:
            event.name = request.POST['name']
            event.description = request.POST['description']
            event.is_public = request.POST['is_public'] == 'public'
            event.from_date = request.POST['from_date']
            event.to_date = request.POST['to_date']
            event.balance = int(request.POST['balance'])
            event.places = int(request.POST['places'])
        
            if request.FILES.get('image') is not None:
                event.image = request.FILES['image']
            emails = [User.objects.filter(username=i.user).first().email for i in EventMember.objects.filter(event_id=event_id)]
            thread = Thread(target=rassylka,
                                         args=("Изменения", f"Здравствуйте, на событии {event.name} произошли изменения. Обратите, пожалуйста, внимание!", emails))
            thread.start()
            event.save()
        except Exception as ex:
            print(ex)
            return redirect(f'/edit_event?event_id={event_id}')
        return redirect('/myevents')
    else:
        context = {
            'event':event
        }
        return render(request, 'edit_event.html', context=context)
    

def delete_event(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    event_id = int(request.GET['event_id'])

    event = Event.objects.filter(id=event_id).first()
    if event.author != _login:
        return redirect('/login')
    emails = [User.objects.filter(username=i.user).first().email for i in EventMember.objects.filter(event_id=event_id)]
    for i in EventMember.objects.filter(event_id=event_id).all():
        i.delete()
    event.delete()
    
    thread = Thread(target=rassylka,
                                 args=("Изменения", f"Здравствуйте, событие {event.name} удалили!", emails))
    thread.start()
    return redirect('/myevents')


def add_shop_item(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    if request.POST:
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        image = request.FILES['image']
        message_upon_receipt = request.POST['message_upon_receipt']
        si = ShopItem(name=name, description=description, price=price, image=image, message_upon_receipt=message_upon_receipt)
        si.save()
        return redirect('/shop')
    else:
        return render(request, 'add_item.html')
    

def shop(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username

    ub = UserBalance.objects.filter(user=_login).first()

    items = ShopItem.objects.filter(buyed=False).all().order_by('-id')

    context = {
        'items': items,
        'balance': ub.balance
    }

    return render(request, 'shop.html', context=context)


def view_shop_item(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    item_id = int(request.GET['item_id'])
    item = ShopItem.objects.filter(id=item_id, buyed=False).first()
    if item is None:
        return redirect('/shop')
    
    context = {
        'item': item,
    }

    return render(request, 'view_shop_item.html', context=context)


def add_balls(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    event_id = int(request.GET['event_id'])

    event = Event.objects.filter(id=event_id).first()
    if event.author != _login:
        return redirect('/login')
    
    if (date.today() - event.to_date).days <= 0:
        return redirect('/login')

    users = []
    em = EventMember.objects.filter(event_id=event_id).all()
    for i in em:
        users.append(User.objects.filter(username=i.user).first())

    if request.POST:
        users2addballs = request.POST.getlist('users')
        for i in users2addballs:
            ub = UserBalance.objects.filter(user=i).first()
            ub.balance += event.balance
            ub.save()
        emails = [User.objects.filter(username=i).first().email for i in users2addballs]
        thread = Thread(target=rassylka,
                                 args=("Баллы", f"Здравствуйте, вам начислено {event.balance} баллов! Продолжайте учавствовать в мероприятиях", emails))
        thread.start()
        event.delete()
        return redirect('/')
    else:
        context = {
            'users': users
        }
        return render(request, 'add_balls.html', context=context)
    

def buy(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    item_id = int(request.GET['item_id'])
    item = ShopItem.objects.filter(id=item_id, buyed=False).first()

    ub = UserBalance.objects.filter(user=_login).first()
    if ub.balance < item.price:
        return redirect('/shop')

    item.buyed = True
    item.buyer = _login

    ub.balance -= item.price
    ub.save()

    item.save()

    return redirect('/my_buyed_items')


def my_buyed_items(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    items = ShopItem.objects.filter(buyed=True, buyer=_login).all().order_by('-id')

    context = {
        'items': items,
    }

    return render(request, 'my_buyed_items.html', context=context)


def edit_items(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    
    items = ShopItem.objects.filter(buyed=False).all().order_by('-id')

    context = {
        'items': items,
    }

    return render(request, 'edit_items.html', context=context)


def edit_item(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    
    item_id = int(request.GET['item_id'])
    si = ShopItem.objects.filter(id=item_id).first()
    
    if request.POST:
        try:
            si.name = request.POST['name']
            si.description = request.POST['description']
            si.price = request.POST['price']
            si.message_upon_receipt = request.POST['message_upon_receipt']
            if request.FILES.get('image') is not None:
                si.image = request.FILES['image']
        
            si.save()
        except:
            return redirect(f'/edit_item?item_id={item_id}')
        return redirect('/edit_items')
    else:
        context = {
            'item': si
        }
        return render(request, 'edit_item.html', context=context)


def delete_item(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    
    item_id = int(request.GET['item_id'])
    si = ShopItem.objects.filter(id=item_id).first()
    si.delete()
    return redirect('/edit_items')


def send_faq(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()

    if request.POST:
        author = user.username
        message = request.POST['message']
        faq = FAQMessage(author=author, message=message)
        faq.save()
        return redirect('/')
    else:
        return render(request, 'send_faq.html')
    

def read_faq_messages(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    
    faqs = FAQMessage.objects.all().order_by('-id')

    context = {
        'faqs': faqs
    }

    return render(request, 'read_faqs.html', context=context)


def view_faq(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    faq_id = int(request.GET['faq_id'])
    faq = FAQMessage.objects.filter(id=faq_id).first()
    context = {
        'faq': faq
    }
    return render(request, 'view_faq.html', context=context)


def delete_faq(request):
    if not request.user.is_authenticated:
       return redirect('/login')
    _login = request.user.username
    user = User.objects.filter(username=_login).first()
    if not user.is_staff:
        return redirect('/login')
    faq_id = int(request.GET['faq_id'])
    faq = FAQMessage.objects.filter(id=faq_id).first()
    faq.delete()
    return redirect('/read_faqs')


def profile(request):
    return render(request, 'profile.html')


def private_cabinet(request):
    return render(request, 'private_cabinet.html')


def events_my(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    _login = request.user.username
    
    events_ids = [i.event_id for i in EventMember.objects.filter(user=_login)]
    all_events = [Event.objects.filter(id=event_id).first() for event_id in events_ids]
    # events = []
    # for i in all_events:
    #     if not i.can_add_balls():
    #         events.append(i)
    context = {
        'events': all_events
    }
    return render(request, 'eventsmy.html', context=context)