import os
import json
import requests
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    OpenProjectAuthorizeSerializer,
    OpenProjectCallbackSerializer,
    OpenProjectProjectsSerializer,
    # OpenProjectTasksSerializer,
    # OpenProjectCreateProjectSerializer,
    # OpenProjectCreateTaskSerializer,
    # OpenProjectUpdateProjectSerializer,
    OpenProjectUpdateTaskSerializer
)
from django.shortcuts import redirect

load_dotenv()

@api_view(['GET'])
def authorize(request):
    client_id = "MRBQ9-ZvovGTJM9rLRbFIEG7A8fMVP-GTKuro8S4XTI"
    redirect_uri = os.getenv('redirect_uri') 
    scope = os.getenv('scope') 
    authorization_url = (
        f"https://bsts.openproject.com/oauth/authorize"
        f"?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
    )

    serializer = OpenProjectAuthorizeSerializer({"authorization_url": authorization_url})
    return redirect(authorization_url)

@api_view(['GET'])
def callback(request):
    code = request.GET.get('code')
    serializer = OpenProjectCallbackSerializer(data={'code': code})
    
    if serializer.is_valid():
        access_token = serializer.save().get('access_token')
        request.session['access_token'] = access_token
        return redirect('integration:projects')
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def fetch_projects(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('integration:authorize')

    serializer = OpenProjectProjectsSerializer()
    projects = serializer.get_projects(access_token)
    formatted_project = []
    for p in projects['_embedded']['elements']:
        formatted_project.append(f"project id -> {p["id"]}  project name -> {p["name"]} ")
    return Response(formatted_project) 


@api_view(['GET'])
def filter_tasks_by_project(request, project_id):
    access_token = request.session.get('access_token')
    if not access_token:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
    tasks_url = "https://bsts.openproject.com/api/v3/work_packages"
    filters = json.dumps([{"project": {"operator": "=", "values": [str(project_id)]}}])
    params = {
        'filters': filters
    }
    try:
        response = requests.get(tasks_url, headers={"Authorization": f"Bearer {access_token}"}, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        tasks = response.json()
        formatted_tasks = []
        for t in tasks['_embedded']["elements"]:
            task = f"{t['id']} {t['subject']} {t['_links']['project']['title']} {t['_links']['type']['title']} {t['_links']['status']['title']} "
            formatted_tasks.append(task)
        
        return Response(tasks)
    
    except requests.exceptions.HTTPError as e:
        return Response({"detail": str(e)}, status=e.response.status_code)

@api_view(['PATCH'])
def update_task(request, task_id):
    access_token = request.session.get('access_token')
    if not access_token:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
    task_url = f"https://bsts.openproject.com/api/v3/work_packages/{task_id}"
    
    try:
        # Fetch current task data to get lock version
        current_task_response = requests.get(task_url, headers={"Authorization": f"Bearer {access_token}"})
        current_task_response.raise_for_status()
        current_task = current_task_response.json()
        
        # Include lock version in request data
        request.data['lock_version'] = current_task.get('lockVersion')
        
        serializer = OpenProjectUpdateTaskSerializer(instance=current_task, data=request.data)

        # Print or log request data and validated data for debugging
        print(f"Request Data: {request.data}")
        if serializer.is_valid():
            print(f"Validated Data: {serializer.validated_data}")
        
        if serializer.is_valid():
            # Perform the update using the serializer's update method
            updated_task = serializer.update(instance=current_task, validated_data=serializer.validated_data, access_token=access_token)
            return Response(updated_task, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {str(e)}")
        return Response({"detail": str(e)}, status=e.response.status_code)
    except KeyError as e:
        print(f"KeyError: {str(e)}")
        return Response({"detail": f"KeyError: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    
    
# @api_view(['GET'])
# def fetch_tasks(request):
#     access_token = request.session.get('access_token')
#     if not access_token:
#         return redirect('integration:authorize')

#     serializer = OpenProjectTasksSerializer()
#     tasks = serializer.get_tasks(access_token)
#     formatted_tasks = []
#     for t in tasks['_embedded']["elements"]:
#         task = f"{t['id']} {t['subject']} {t['_links']['project']['title']} {t['_links']['type']['title']} {t['_links']['status']['title']} "
#         formatted_tasks.append(task)
    
#     # return Response(tasks)
#     return Response(formatted_tasks)


# @api_view(['POST'])
# def create_project(request):
#     access_token = request.session.get('access_token')
#     if not access_token:
#         return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
#     serializer = OpenProjectCreateProjectSerializer(data=request.data)
#     if serializer.is_valid():
#         project = serializer.create(validated_data=serializer.validated_data, access_token=access_token)
#         return Response(project, status=status.HTTP_201_CREATED)
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# {
#     "name": "New Project Name",
#     "identifier": "new-project-identifier",
#     "description": "This is a description of the new project."
# }


# @api_view(['POST'])
# def create_task(request):
#     access_token = request.session.get('access_token')
#     if not access_token:
#         return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
#     serializer = OpenProjectCreateTaskSerializer(data=request.data)
#     if serializer.is_valid():
#         task = serializer.create(validated_data=serializer.validated_data, access_token=access_token)
#         return Response(task, status=status.HTTP_201_CREATED)
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# {
#     "subject": "New Task Subject",
#     "description": "This is a description of the new task.",
#     "project_id": 1,
#     "type_id": 2,
#     "status_id": 7
# }

# @api_view(['PATCH'])
# def update_project(request, project_id):
#     access_token = request.session.get('access_token')
#     if not access_token:
#         return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
#     project_url = f"https://bsts.openproject.com/api/v3/projects/{project_id}"
    
#     serializer = OpenProjectUpdateProjectSerializer(data=request.data)
#     if serializer.is_valid():
#         try:
#             # Fetch current project data to pass as instance
#             current_project_response = requests.get(project_url, headers={"Authorization": f"Bearer {access_token}"})
#             current_project = current_project_response.json()
            
#             updated_project = serializer.update(current_project, validated_data=serializer.validated_data, access_token=access_token)
#             return Response(updated_project, status=status.HTTP_200_OK)
#         except requests.exceptions.HTTPError as e:
#             return Response({"detail": str(e)}, status=e.response.status_code)
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# {
#     "name": "Updated Project",
#     "description": "This is a description of the new project."
# }


# @api_view(['DELETE'])
# def delete_project(request, project_id):
#     access_token = request.session.get('access_token')
#     if not access_token:
#         return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
#     project_url = f"https://bsts.openproject.com/api/v3/projects/{project_id}"
    
#     try:
#         response = requests.delete(project_url, headers={"Authorization": f"Bearer {access_token}"})
#         response.raise_for_status()  # Raise an error for bad responses
#         return Response({"detail": "Project deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
#     except requests.exceptions.HTTPError as e:
#         return Response({"detail": str(e)}, status=e.response.status_code)
    

# @api_view(['DELETE'])
# def delete_task(request, task_id):
#     access_token = request.session.get('access_token')
#     if not access_token:
#         return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
#     task_url = f"https://bsts.openproject.com/api/v3/work_packages/{task_id}"
    
#     try:
#         response = requests.delete(task_url, headers={"Authorization": f"Bearer {access_token}"})
#         response.raise_for_status()  # Raise an error for bad responses
#         return Response({"detail": "Task deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
#     except requests.exceptions.HTTPError as e:
#         return Response({"detail": str(e)}, status=e.response.status_code)