from django.urls import path
from . import views

app_name = 'integration'

urlpatterns = [
    path('authorize/', views.authorize.as_view(), name='authorize'),
    path('callback/', views.callback.as_view(), name='callback'),
    path('projects/', views.fetch_projects.as_view(), name='projects'),
    path('add_time_entry/', views.create_time_entry.as_view(), name='create-time-entry'),
    path('tasks_by_project/<int:project_id>/', views.filter_tasks_by_project.as_view(), name='filter_tasks_by_project'),
    # path('tasks/', views.fetch_tasks, name='tasks'),
    # path('create_project/', views.create_project, name='create_project'),
    # path('create_task/', views.create_task, name='create_task'),
    # path('update_project/<int:project_id>/', views.update_project, name='update_project'),
    # path('update_task/<int:task_id>/', views.update_task, name='update_task'),
    # path('delete_project/<int:project_id>/', views.delete_project, name='delete_project'),
    # path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    
]
