from unicodedata import name
from django.urls import path
from . import views as ev

urlpatterns = [
    path('', ev.login, name='login'),
    path('validation', ev.validation, name='validation'),
    path('landingpage/', ev.landingpage, name='landingpage'),
    path('commodity/', ev.commodity, name='commodity'),
    path('getsheetdata/', ev.getsheetdata, name='getsheetdata'),
    path('uploaddata/', ev.uploaddata, name='uploaddata'),
    path('detect_document/', ev.detect_document, name='detect_document'),
    path('localize_objects/', ev.localize_objects, name="localize_objects"),
    path('registration/', ev.registration, name='registration'),
    path('ocr/', ev.ocr, name='ocr'),
    path('objectcount/', ev.objectcount, name='objectcount'),
    path('massupdate/', ev.massupdate, name='massupdate'),

    # stock
    path('stock_screener/', ev.stock_screener, name='stock_screener'),
    path('stock_predictions/', ev.stock_predictions, name='stock_predictions'),
    path('graph/<str:ticker>/', ev.graph, name='graph'),
    path('user_settings/', ev.user_settings, name='user_settings'),
    path('usersedit/', ev.usersedit, name='usersedit'),
    path('changepw/', ev.changepw, name='changepw'),
    path('adminpanel/', ev.adminpanel, name='adminpanel'),
    path('saveuser/', ev.saveuser, name='saveuser'),
    path('useredit/', ev.useredit, name='useredit'),
    path('delete_user/<int:id>', ev.delete_user, name='delete_user'),
    path('get_user/', ev.get_user, name='get_user'),
    path('customer/', ev.customer, name='customer'),
    path('pdf/', ev.pdf, name='pdf'),

]
