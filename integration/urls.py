from django.urls import path
from . import views

app_name = 'integration'

urlpatterns = [
    path('authorize/', views.authorize, name='authorize'),
    path('callback/', views.callback, name='callback'),
    path('projects/', views.fetch_projects, name='projects'),
    # path('tasks/', views.fetch_tasks, name='tasks'),
    # path('create_project/', views.create_project, name='create_project'),
    # path('create_task/', views.create_task, name='create_task'),
    # path('update_project/<int:project_id>/', views.update_project, name='update_project'),
    path('update_task/<int:task_id>/', views.update_task, name='update_task'),
    # path('delete_project/<int:project_id>/', views.delete_project, name='delete_project'),
    # path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('tasks_by_project/<int:project_id>/', views.filter_tasks_by_project, name='filter_tasks_by_project')
]
