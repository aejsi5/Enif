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
            print(mes)
            #1. Letzte human Request nehmen
            rhis = Enif_Session_History.objects.filter(Session=s, D=False, Intent_Answer=None, Enif_System_Answer=None).order_by('Inserted').last()
            if rhis:
                req = Enif_Request.objects.get(ID=rhis.Request.ID, D=False)
                #2. Intent aus dieser Herausnehmen
                #3. Je nach Intent eine Funktion im Chatbot ansprechen
                if req.Intent:
                    self.intent_handler(s, req.Intent.ID)
                else: 
                    self.intent_handler(s, None)
        #5. komplette His rendern
        res["Enif"]["Messages"] = self.his_renderer(s)
        if mes and req.Intent.Tag in ['contact', 'invoice']:
            res["Enif"]["Messages"].append(self.dialog(req.Intent.Tag))
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
        return res

    def intent_handler(self, session, intent):
        #4. Die Antwort auf den Intent in die His schreiben
        intent = Intent.objects.get(ID=intent, D=False)
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

    def dialog(self, intenttag):
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
                        "Name": "enif_input_akz"
                    },
                    {
                        "Placeholder": "Rechnungsnummer",
                        "Intent": 18,
                        "Type": "text",
                        "Name": "enif_input_rechnungsnummer"
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
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            actual = datetime.now()
            s = Enif_Session.objects.get(Token=session, D=False, Valid_Until__gte=actual)
        except Enif_Session.DoesNotExist:
            return HttpResponse(status=404)
        rdata_im = request.data
        rdata = rdata_im.copy()
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
            enif_r.Intent_Accuracy= prediction['ACCURACY']
            enif_r.save()
        else:
            i = Intent.objects.get(ID=rdata['Intent'])
            enif_r.Intent = i
            enif_r.Intent_Accuracy = 1
            enif_r.save()
        his = Enif_Session_History(Session=s, Request=enif_r)
        his.save()
        r = Enif_Request.objects.get(Session=s, D=False, ID=enif_r.ID)
        serializer = Basic_Enif_Request_Serializer(r, many=False)
        res = {
            'data': serializer.data
        }
        return Response(res, status=status.HTTP_200_OK)
        


