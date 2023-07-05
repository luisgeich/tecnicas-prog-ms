from django.urls import path
from . import views

# URLConf   
urlpatterns = [
    path('students/', views.StudentViews.as_view()),
    path('students/<str:id>/', views.StudentDetailView.as_view()),
    path('students/<str:id>/features/', views.StudentFeatureView.as_view()),

    path('features/', views.FeatureViews.as_view()),
    path('features/<str:id>/', views.FeatureDetailView.as_view()),

    path('states/', views.StateViews.as_view()),
    path('states/<str:id>/', views.StateDetailView.as_view()),

    path('behaviors/', views.BehaviorViews.as_view()),
    path('behaviors/<str:id>/', views.BehaviorDetailView.as_view()),
    
    path('infer/states/', views.StudentStateInferatorView.as_view()),
    path('infer/states/<str:idStudent>/', views.StudentStateInferatorView.as_view()),

    path('infer/behaviors/', views.StudentBehaviorInferatorView.as_view()),
    path('infer/behaviors/<str:idStudent>/', views.StudentBehaviorInferatorView.as_view()),

    path('get-csrf-token/', views.get_csrf_token),
]