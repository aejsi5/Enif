from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from datetime import datetime
from datetime import timedelta
from django.conf import settings
import os
import secrets

# Create your models here.
class Enif_User(AbstractUser):
    pass

class Whitelist(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Host = models.CharField('Host', max_length=50, null=False, blank=False)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Host)

    class Meta:
        app_label = "enif_app"

class Intent(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Name = models.CharField('Name', max_length=50, null=False, blank=False)
    Tag = models.CharField('Tag', max_length=30, unique=True, null=False, blank=False)
    Des = models.CharField('Beschreibung', max_length=255, blank=True, null=True)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Name)

    class Meta:
        app_label = "enif_app"

class Stopword(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Pattern = models.CharField('Pattern', max_length=50, unique=True, null=False, blank=False)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Pattern)

    class Meta:
        app_label = "enif_app"

class Pattern(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Intent = models.ForeignKey(Intent, on_delete=models.CASCADE)
    Pattern = models.CharField('Pattern', max_length=50, null=False, blank=False)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Pattern)

    class Meta:
        app_label = "enif_app"
        unique_together = ('Intent', 'Pattern',)

def create_session_token():
    pre = secrets.token_urlsafe(8)
    suf = secrets.token_urlsafe(8)
    last_Session = Enif_Session.objects.all().order_by('ID').last()
    if last_Session:
        return pre+str(last_Session.ID)+suf
    else:
        return pre+suf

def set_valid_until():
    #Nicht löschen
    print("")

class Enif_Session(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Token = models.CharField('Token', max_length=50, null=False, blank=False, default=create_session_token)
    Source = models.CharField('Quelle', max_length=50, null=False, blank=False)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    User_Feedback = models.BooleanField('Hilfreich', default=None, null=True)
    Valid_Until = models.DateTimeField('Gültig bis', null=False, blank=False)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Token)

    class Meta:
        app_label = "enif_app"

class Enif_Request(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Session = models.ForeignKey(Enif_Session, on_delete=models.CASCADE)
    Pattern = models.CharField('Pattern', max_length=100, null=False, blank=False)
    Predict = models.BooleanField('Verstehen', default=True)
    Intent = models.ForeignKey(Intent, on_delete=models.CASCADE, null=True, blank=True)
    Intent_Accuracy = models.FloatField('Genauigkeit', null=True, blank=True)
    User_Feedback = models.BooleanField('Hilfreich', default=None, null=True)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Inserted)

    class Meta:
        app_label = "enif_app"

class Enif_Intent_Answer(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Intent = models.ForeignKey(Intent, on_delete=models.CASCADE, null=True, blank=True)
    Answer = models.TextField('Antwort', null=True, blank=True)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Answer)

    class Meta:
        app_label = "enif_app"

class Enif_System_Answer(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Answer = models.CharField('Antwort', max_length=255, null=True, blank=True)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.Answer)

    class Meta:
        app_label = "enif_app"

class Enif_Session_History(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    Session = models.ForeignKey(Enif_Session, on_delete=models.CASCADE)
    Request = models.ForeignKey(Enif_Request, on_delete=models.CASCADE, null=True, blank=True)
    Intent_Answer = models.ForeignKey(Enif_Intent_Answer, on_delete=models.CASCADE, null=True, blank=True)
    Enif_System_Answer = models.ForeignKey(Enif_System_Answer, on_delete=models.CASCADE, null=True, blank=True)
    Enif_Info = models.TextField('Info', null=True, blank=True)
    Inserted = models.DateTimeField('Angelegt am', auto_now_add=True)
    LU = models.DateTimeField('Geändert am', auto_now=True)
    D = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.ID)

    class Meta:
        app_label = "enif_app"

class Invoices(models.Model):
    ID = models.AutoField('ID', primary_key=True)
    AKZ = models.CharField('Amtliches Kennzeichen', max_length=10, null=True, blank=True)
    IKZ = models.CharField('Internes Kennzeichen', max_length=10, null=False, blank=False)
    Case = models.CharField('Vorgangsnummer', max_length=10, null=False, blank=False)
    Inv_Date = models.DateField('Rechnungsdatum', null=True, blank=True)
    Inv_No = models.CharField('Rechnungsnummer', max_length=25, null=False, blank=False)
    Price_net =  models.DecimalField('Preis netto',max_digits=6, decimal_places=2, null=True, blank=True)
    Price_gros = models.DecimalField('Preis brutto',max_digits=6, decimal_places=2, null=True, blank=True)
    Status = models.CharField('Status', max_length=25, null=True, blank=True)
    Exported = models.BooleanField('Kreditorisch exportiert', default=False)

    def __str__(self):
        return str(self.ID)

    class Meta:
        app_label = "enif_app"
