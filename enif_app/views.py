from keras.models import load_model
import spacy
from keras.models import Sequential
import numpy as np
from keras.optimizers import SGD
from keras.layers import Dense, Activation, Dropout
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import *
import requests
import random
from .models import *
from .serializers import *
from .permissions import *
from .preprocessing import *
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import json
log = logging.getLogger(__name__)

# Create your views here.
def index(request):
    #log.debug("Hey there it works!!")
    #log.info("Hey there it works!!")
    #log.warn("Hey there it works!!")
    #log.error("Hey there it works!!")
    return render(request, 'enif.html')


def run_DNN_Admin(request, *args, **kwargs):
    if request.user.has_perm('dfa_App.enif_dnn_admin'):
        try:
            I = DNN_Admin()
            I.start_preprocessing()
            I.start_dnn_modeling()
        except:
            log.error('Error while Preprocessing')
            HttpResponse(status=400)
        return HttpResponse(status=200)
    log.error('Permission denied')
    return HttpResponse(status=403)

class DNN_Admin():
    def start_preprocessing(self):
        self.PP = PreProcessor()
        self.PP.get_training_data()

    def start_dnn_modeling(self):
        model = Sequential()
        model.add(Dense(128, input_shape=(len(self.PP.training[0]),), activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(83, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(len(self.PP.output[0]), activation='softmax'))
        sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
        model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
        hist = model.fit(self.PP.training, self.PP.output,
                         epochs=500, batch_size=5, verbose=1)
        base_dir = settings.MEDIA_ROOT
        filename = os.path.join(base_dir, str("dnn/chatbot_model.h5"))
        model.save(filename, hist)


class Chatbot_Api(APIView):
    permission_classes = [WhitelistPermission]

    def get(self, request, session):
        res = {'Enif': {} }
        try:
            actual = datetime.now()
            s = Enif_Session.objects.get(Token=session, D=False, Valid_Until__gte=actual)
            res["Enif"]["Session"] = {
                "Token": s.Token,
                "Source": s.Source,
                "User_Feedback": s.User_Feedback,
                "Valid_Until": s.Valid_Until
            }
        except Enif_Session.DoesNotExist:
            log.error('Session does not exist')
            return Response({}, status=status.HTTP_403_FORBIDDEN)
        mes = Enif_Session_History.objects.filter(Session=s, D=False).order_by('Inserted')
        if not mes:
            hello = self.say_hello(s)
        else:
            #1. Letzte human Request nehmen
            rhis = Enif_Session_History.objects.filter(Session=s, D=False, Intent_Answer=None, Enif_System_Answer=None, Enif_Info=None).order_by('Inserted').last()
            if rhis:
                req = Enif_Request.objects.get(ID=rhis.Request.ID, D=False)
        #His rendern
        res["Enif"]["Messages"] = self.his_renderer(s)
        if mes and req.Intent.Tag in ['contact', 'invoice', 'carinfo']:
            res["Enif"]["Messages"].append(self.options(req.Intent.Tag))
        elif not mes:
            res["Enif"]["Messages"].append(self.options('hello'))
        return Response(res, status=status.HTTP_200_OK)

    def his_renderer(self, session):
        res = []
        try:
            his = Enif_Session_History.objects.filter(Session=session, D=False)
        except Enif_Session_History.DoesNotExist:
            return res
        for h in his:
            if h.Request:
                res.append({"ID": h.pk, "Source": "User", "Message_Type": "PlainText", "Text": h.Request.Pattern, "Timestamp": h.Inserted})
            elif h.Intent_Answer:
                res.append({"ID": h.pk, "Source": "Enif", "Message_Type": "PlainText", "Text": h.Intent_Answer.Answer, "Timestamp": h.Inserted})
            elif h.Enif_System_Answer:
                res.append({"ID": h.pk, "Source": "Enif", "Message_Type": "PlainText", "Text": h.Enif_System_Answer.Answer, "Timestamp": h.Inserted})
            elif h.Enif_Info:
                res.append({"ID": h.pk, "Source": "Enif", "Message_Type": "PlainText", "Text": h.Enif_Info, "Timestamp": h.Inserted})
        return res

    def intent_handler(self, session, intent):
        #4. Die Antwort auf den Intent in die His schreiben
        intent_tag = intent.Tag
        try:
            options = Enif_Intent_Answer.objects.filter(Intent=intent, D=False)
            i = random.choice(options)
            his = Enif_Session_History(Session=session, Intent_Answer=i)
            his.save()
        except IndexError:
            not_understood =[10,11,12]
            i = random.choice(not_understood)
            Ans = Enif_System_Answer.objects.get(ID=i, D=False)
            his = Enif_Session_History(Session=session, Enif_System_Answer=Ans)
            his.save()

    def input_handler(self, session_obj, intenttag, input_data):
        log.info('Input_handler')
        log.debug(intenttag)
        log.debug(input_data)
        if intenttag == 'invoice':
            try:
                akz = input_data['enif_input_akz']
                rg = Invoice_Api().normalize(input_data['enif_input_rechnungsnummer'])
            except:
                log.error("Invoice Inputs not set", exc_info=True)
            try:
                Inv = Invoices.objects.filter(AKZ=akz, Inv_No=rg).order_by('-ID')
                if not Inv:
                    Inv = Invoices.objects.filter(IKZ=akz, Inv_No=rg).order_by('-ID')
                if not Inv:
                    self.error_msg(session_obj, "Ich habe leider keine Rechnung gefunden. Bitte versuche es erneut.")
                    return
            except:
                log.error("Invoice not found", exc_info=True)
            latest_Inv= Inv[0]
            return self.disclosure(session_obj, intenttag, latest_Inv)
        elif intenttag == 'carinfo':
            try:
                vin = input_data['enif_input_vi']
            except:
                log.error("Invoice Inputs not set", exc_info=True)
            try:
                Car = Vehicle.objects.filter(AKZ=vin).order_by('-ID')
                if not Car:
                    Car = Vehicle.objects.filter(IKZ=vin).order_by('-ID')
                if not Car:
                    Car = Vehicle.objects.filter(FIN=vin).order_by('-ID')
                if not Car:
                    self.error_msg(session_obj, "Ich habe leider kein Fahrzeug gefunden. Bitte versuche es erneut.")
                    return
            except:
                log.error("Vehicle not found", exc_info=True)
            last_Car= Car[0]
            return self.disclosure(session_obj, intenttag, last_Car)

    def disclosure(self, session_obj, intenttag, obj):
        log.debug("Params")
        log.debug(session_obj)
        log.debug(intenttag)
        log.debug(obj)
        if intenttag == 'invoice':
            try:
                his = Enif_Session_History(Session=session_obj, Enif_Info="Ich habe deine Rechnung gefunden.")
                his.save()
            except:
                log.error('Fatal Error', exc_info=True)
            if obj.Inv_No and obj.Case and obj.Inv_Date:
                text = "Die Rechnung mit der Nummer {} (normalisiert) vom {} läuft bei uns unter der Vorgangsnummer {}".format(obj.Inv_No, obj.Inv_Date, obj.Case)
            elif obj.Inv_No and obj.Case and not obj.Inv_Date:
                text = "Die Rechnung mit der Nummer {} (normalisiert) läuft bei uns unter der Vorgangsnummer {}".format(obj.Inv_No, obj.Case)
            try:
                his = Enif_Session_History(Session=session_obj, Enif_Info=text)
                his.save()
            except:
                log.error('Fatal Error', exc_info=True)
            if obj.Exported:
                text = "Die Rechnung wurde bereits bearbeitet. Das Geld sollte in Kürze bei Ihnen eingehen."
            elif obj.Status:
                text = "Die Rechnung befindet sich bei uns im Status {}. Bitte haben Sie noch etwas Geduld. Sollte die Rechnung überfällig sein können Sie sich gern an tim.rechnungen@dpdhl.com wenden.".format(obj.Status)
            elif not obj.Exported or not obj.Status:
                text: "Leider liegt mir zu dieser Rechnung noch kein Bearbeitungsstatus vor. Bitte versuche es morgen noch einmal. Du kannst dich auch gern an tim.rechnungen@dpdhl.com wenden."
            try:
                his = Enif_Session_History(Session=session_obj, Enif_Info=text)
                his.save()
            except:
                log.error('Fatal Error', exc_info=True)
            return
        elif intenttag == 'carinfo':
            try:
                his = Enif_Session_History(Session=session_obj, Enif_Info="Ich habe das Fahrzeug gefunden.")
                his.save()
            except:
                log.error('Fatal Error', exc_info=True)
            try:
                text = '<table class="enif_tbl"><tr><td>AKZ:</td><td>'+ str(obj.AKZ) +'</td><td>IKZ:</td><td>' + str(obj.IKZ) + '</td></tr><tr><td>FIN:</td><td>' + str(obj.FIN) +'</td></tr><tr><td>Hersteller:</td><td>' + str(obj.Make) + '</td></tr><tr><td>Modell:</td><td>' + str(obj.Model) + '</td></tr><tr><td>Baujahr:</td><td>' + str(obj.Baujahr) + '</td></tr><tr><td>Servicevetrag:</td><td>' + str(obj.Servicevertrag) + '</td></tr><tr><td>Servicevertragsgeber:</td><td>' + str(obj.Servicevertragsgeber) + '</td></tr><tr><td>Reifenvertrag</td><td>' + str(obj.Reifenvertrag) + '</td></tr><tr><td>Reifendienstleister</td><td>' + str(obj.Reifendienstleister) + '</td></tr><tr><td>Bereifung:</td><td>' + str(obj.Bereifung) + '</td></tr></table>'
            except:
                log.error('Fatal Error', exc_info=True)
                return
            try:
                his = Enif_Session_History(Session=session_obj, Enif_Info=text)
                his.save()
            except:
                log.error('Fatal Error', exc_info=True)
            return
            

    def error_msg(self, session, msg="Etwas ist schiefgelaufen. Bitte versuche es später erneut"):
        log.warning("Session: {} Error-Msg: {}".format(session.Token, msg))
        his = Enif_Session_History(Session=session, Enif_Info=msg)
        his.save()

    def options(self, intenttag):
        if intenttag == "contact":
            return {
                "ID": None,
                "Source": "Enif",
                "Message_Type": "Options",
                "Options": [
                    {
                        "Text": "Fz bis 2,8t",
                        "Intent": 11,
                        "Symbol": "fas fa-truck"
                    },
                    {
                        "Text": "Fz über 2,8t",
                        "Intent": 12,
                        "Symbol": "fas fa-truck-moving"
                    },
                    {
                        "Text": "Wechselbehälter",
                        "Intent": 15,
                        "Symbol": "fas fa-truck-loading"
                    },
                    {
                        "Text": "Werkstattportal",
                        "Intent": 14,
                        "Symbol": "fas fa-toolbox"
                    },
                    {
                        "Text": "Firmenwagen",
                        "Intent": 13,
                        "Symbol": "fas fa-car-side"
                    },
                    {
                        "Text": "Rechnungen",
                        "Intent": 16,
                        "Symbol": "fas fa-file-invoice-dollar"
                    }
            ]}
        elif intenttag == 'hello':
            return {
                "ID": None,
                "Source": "Enif",
                "Message_Type": "Options",
                "Options": [
                    {
                        "Text": "Kontakt",
                        "Intent": 7,
                        "Symbol": "fas fa-phone"
                    },
                    {
                        "Text": "Rechnungsstatus",
                        "Intent": 18,
                        "Symbol": "fas fa-file-invoice-dollar"
                    },
                    {
                        "Text": "Fahrzeuginfos",
                        "Intent": 19,
                        "Symbol": "fas fa-car-side"
                    },
                    {
                        "Text": "Chatbot",
                        "Intent": 4,
                        "Symbol": "fas fa-robot"
                    },
                    {
                        "Text": "Feedback",
                        "Intent": 21,
                        "Symbol": "fas fa-car-side"
                    }
            ]}
        elif intenttag == 'invoice':
            return {
                "ID": None,
                "Source": "Enif",
                "Message_Type": "Inputs",
                "Inputs": [
                    {
                        "Placeholder": "AKZ/IKZ",
                        "Intent": 18,
                        "Type": 'Text',
                        "Name": "enif_input_akz",
                        "Width": '45%'
                    },
                    {
                        "Placeholder": "Rg-Nr",
                        "Intent": 18,
                        "Type": "text",
                        "Name": "enif_input_rechnungsnummer",
                        "Width": '45%'
                    }
                ]}
        elif intenttag == 'carinfo':
            return {
                "ID": None,
                "Source": "Enif",
                "Message_Type": "Inputs",
                "Inputs": [
                    {
                        "Placeholder": "AKZ/IKZ/FIN",
                        "Intent": 19,
                        "Type": 'Text',
                        "Name": "enif_input_vi",
                        "Width": '95%'
                    }
                ]}

    def do_predict(self, Enif_Request_Obj):
        base_dir = settings.MEDIA_ROOT
        filename = os.path.join(base_dir, str("dnn/chatbot_model.h5"))
        self.model = load_model(filename)
        filename = os.path.join(base_dir, str("dnn/preprocessed_data.json"))
        with open(filename, encoding='utf-8') as f:
            data = json.load(f)
            self.labels = data['labels']
        bag = bag_of_words(Enif_Request_Obj.Pattern)
        bag = np.array([bag])
        if settings.DEBUG == True:
            print(bag)
        res = self.model.predict(bag)[0]
        if settings.DEBUG == True:
            print(res)
        results_index = np.argmax(res)
        results_val = np.amax(res)
        if results_val < settings.ENIF_OPTIONS['PREDICT_THRESHOLD']:
            res = {
                'Intent': None,
                'ACCURACY': results_val
            }
        else:
            i = self.labels[results_index]
            res = {
                'Intent': i,
                'ACCURACY': results_val
            }
        return res

    def say_hello(self, Session):
        hello_morning = [1,7,2,3]
        hello_mid = [2,3,8]
        hello_eve = [4,6,9]
        res = []

        current = datetime.now()
        current_hour = int(current.strftime("%H"))
        if current_hour < 12:
            #Morgens
            i = random.choice(hello_morning)
        elif current_hour >= 12 and current_hour < 18:
            #Tag
            i = random.choice(hello_mid)
        else:
            i = random.choice(hello_eve)
        try:
            Ans = Enif_System_Answer.objects.get(ID=i, D=False)
            his = Enif_Session_History(Session=Session, Enif_System_Answer=Ans)
            his.save()
            res.append({"ID": his.pk, "Source": "Enif", "Text": Ans.Answer, "Timestamp": his.Inserted})
            Ans = Enif_System_Answer.objects.get(ID=5, D=False)
            his = Enif_Session_History(Session=Session, Enif_System_Answer=Ans)
            his.save()
            res.append({"ID": his.pk, "Source": "Enif", "Text": Ans.Answer, "Timestamp": his.Inserted})
            return res
        except Enif_System_Answer.DoesNotExist:
            return [res.append({"ID": None, "Source": "Enif", "Text": "Hallo, wie kann ich helfen?", "Timestamp": current})]

   
class Enif_Session_Api(APIView):
    permission_classes = [WhitelistPermission]

    def get(self, request, token=None, format=None):
        if not token:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            s = Enif_Session.objects.get(Token=token, D=False)
        except Enif_Session.DoesNotExist:
            return HttpResponse(status=404)
        serializer = Enif_Session_Serializer(s, many=False)
        res = {
            'data': serializer.data
        }
        return Response(res)

    def post(self, request, *args, **kwargs):
        try:
            domain = request.headers.get('Host')
            act = datetime.now() + timedelta(minutes=5)
            data = {'Source': domain,
                    'Valid_Until': act}
            serializer = Enif_Session_Serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                res = {
                    'data': serializer.data
                }
                return Response(res, status=status.HTTP_200_OK)
            else:
                log.error('Serializer Errors')
                log.error(serializer.errors)
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except:
            log.error('Domain not allowed')
            return HttpResponse(status=404)

    def put(self, request, token=None, *args, **kwargs):
        if not token:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            s = Enif_Session.objects.get(Token=token, D=False)
            act = datetime.now() + timedelta(minutes=5)
            s.Valid_Until = act
            s.save()
        except Enif_Session.DoesNotExist:
            log.error('Session does not exist')
            return HttpResponse(status=404)
        serializer = Enif_Session_Serializer(s, many=False)
        res = {
            'data': serializer.data
        }
        return Response(res, status=status.HTTP_200_OK)

class Enif_Request_Api(APIView):
    permission_classes = [WhitelistPermission]

    def get(self, request, session=None, pk=None, format=None):
        if not session:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not pk:
            try:
                s = Enif_Session.objects.get(Token=session, D=False)
                rq = Enif_Request.objects.filter(Session=s, D=False)
            except Enif_Session.DoesNotExist:
                return HttpResponse(status=404)
            except Enif_Request.DoesNotExist:
                return HttpResponse(status=404)
            serializer = Basic_Enif_Request_Serializer(rq, many=True)
            res = {
                'data': serializer.data
            }
            return Response(res)
        else:
            try:
                s = Enif_Session.objects.get(Token=session, D=False)
                rq = Enif_Request.objects.get(Session=s, D=False, ID=pk)
            except Enif_Session.DoesNotExist:
                return HttpResponse(status=404)
            except Enif_Request.DoesNotExist:
                return HttpResponse(status=404)
            serializer = Basic_Enif_Request_Serializer(rq, many=False)
            res = {
                'data': serializer.data
            }
            return Response(res)

    def post(self, request, session=None, format=None):
        if not session:
            log.error('No Session')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            actual = datetime.now()
            s = Enif_Session.objects.get(Token=session, D=False, Valid_Until__gte=actual)
        except Enif_Session.DoesNotExist:
            log.error('No valid Session found')
            return HttpResponse(status=404)
        rdata = request.data
        log.info('request.data')
        log.info(rdata)
        rdata['Session'] = s.ID
        serializer = Full_Enif_Request_Serializer(data=rdata)
        if serializer.is_valid():
            enif_r = serializer.save()
            s.Valid_Until = datetime.now() + timedelta(minutes=5)
            s.save()
        else:
            log.error(serializer.errors)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if enif_r.Predict:
            prediction = Chatbot_Api().do_predict(enif_r)
            if prediction["Intent"]:
                i = Intent.objects.get(ID=prediction['Intent'])
                enif_r.Intent = i
            else:
                i = None
            enif_r.Intent_Accuracy= prediction['ACCURACY']
            enif_r.save()
            his = Enif_Session_History(Session=s, Request=enif_r)
            his.save()
            Chatbot_Api().intent_handler(s, i)
        else:
            if rdata['Inputs']:
                i = Intent.objects.get(ID=rdata['Intent'])
                enif_r.Intent = i
                enif_r.Intent_Accuracy = 1
                enif_r.save()
                his = Enif_Session_History(Session=s, Request=enif_r)
                his.save()
                Chatbot_Api().input_handler(s, i.Tag, rdata['Inputs'])
            else:
                #Option Handling
                i = Intent.objects.get(ID=rdata['Intent'])
                enif_r.Intent = i
                enif_r.Intent_Accuracy = 1
                enif_r.save()
                his = Enif_Session_History(Session=s, Request=enif_r)
                his.save()
                Chatbot_Api().intent_handler(s, i)
        r = Enif_Request.objects.get(Session=s, D=False, ID=enif_r.ID)
        serializer = Basic_Enif_Request_Serializer(r, many=False)
        res = {
            'data': serializer.data
        }
        return Response(res, status=status.HTTP_200_OK)


class Invoice_Api(APIView):
    permission_classes = [WhitelistPermission]

    def normalize(self, input_string):
        res = input_string.replace(' ' , '')
        res = res.replace('-' , '')
        res = res.replace('_' , '')
        res = res.replace('.' , '')
        res = res.replace(':' , '')
        res = res.replace(',' , '')
        res = res.replace(';' , '')
        res = res.replace('+' , '')
        res = res.replace('#' , '')
        res = res.replace('*' , '')
        res = res.replace('~' , '')
        res = res.replace('/' , '')
        res = res.replace('!' , '')
        res = res.replace('?' , '')
        res = res.replace('"' , '')
        res = res.replace("'" , '')
        res = res.replace('§' , '')
        res = res.replace('$' , '')
        res = res.replace('%' , '')
        res = res.replace('&' , '')
        res = res.replace('(' , '')
        res = res.replace(')' , '')
        res = res.replace('=' , '')
        res = res.replace('ß', 'ss')
        res = res.upper()
        return res

