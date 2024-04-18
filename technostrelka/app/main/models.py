from django.db import models
from datetime import date


class UserBalance(models.Model):
    balance = models.IntegerField(default=0)
    user = models.CharField(max_length=150)

    def __str__(self):
        return f"Balance-{self.user} - "+str(self.balance)


class Event(models.Model):
    author = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    is_public = models.BooleanField(default=True)
    description = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField()
    balance = models.IntegerField()
    image = models.ImageField(upload_to='images')
    places = models.IntegerField(default=100)

    def can_add_balls(self):
        return (date.today() - self.to_date).days > 0

    def __str__(self):
        return f"Event-{self.id} - "+self.name

class EventMember(models.Model):
    event_id = models.IntegerField()
    user = models.CharField(max_length=150)

    def __str__(self):
        return f"EventMember-{self.event_id} - "+self.user
    

class ShopItem(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    price = models.IntegerField()
    image = models.ImageField(upload_to='images')
    message_upon_receipt = models.TextField()
    buyed = models.BooleanField(default=False)
    buyer = models.CharField(max_length=150, default='', null=True, blank=True)

    def __str__(self):
        return f"ShopItem-{self.id} - "+self.name
    

class FAQMessage(models.Model):
    author = models.CharField(max_length=150)
    message = models.TextField()

    def __str__(self):
        return f"FAQMessage-{self.id} - "+self.author
