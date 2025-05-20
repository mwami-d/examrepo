from django.urls import path
from .views import *


urlpatterns = [
    path('', pptx, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', user_logout, name='logout'), 
    path('exam/preview-ppt/', exam_ppt_preview, name='exam_ppt_preview'),
    path('create_exam/', create_exam_page, name='create_exam'),
    path('undo_last_exam_action/', undo_last_exam_action, name='undo_last_exam_action'),
]