import os
import json
import requests
from dotenv import load_dotenv
from rest_framework.views import APIView
from rest_framework.response import Response
import logging
from rest_framework import status
from .serializers import (
    OpenProjectAuthorizeSerializer,
    OpenProjectCallbackSerializer,
    OpenProjectProjectsSerializer,
    TimeEntrySerializer
    # OpenProjectTasksSerializer,
    # OpenProjectCreateProjectSerializer,
    # OpenProjectCreateTaskSerializer,
    # OpenProjectUpdateProjectSerializer,
    # OpenProjectUpdateTaskSerializer
)
from django.shortcuts import redirect

logger = logging.getLogger(__name__)
load_dotenv()

class authorize(APIView):
    def get(self, request):
        client_id = "MRBQ9-ZvovGTJM9rLRbFIEG7A8fMVP-GTKuro8S4XTI"
        redirect_uri = os.getenv('redirect_uri')
        scope = os.getenv('scope')
        authorization_url = (
            f"https://bsts.openproject.com/oauth/authorize"
            f"?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
        )
        serializer = OpenProjectAuthorizeSerializer({"authorization_url" : authorization_url})

        return redirect(authorization_url)


class callback(APIView):
    def get(self, request):
        code = request.GET.get('code')
        serializer = OpenProjectCallbackSerializer(data={'code': code})
        
        if serializer.is_valid():
            access_token = serializer.save().get('access_token')
            request.session['access_token'] = access_token
            return redirect('integration:projects')
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class fetch_projects(APIView):
    def get(self, request):
        access_token = request.session.get('access_token')
        if not access_token:
            return redirect('integration:authorize')

        serializer = OpenProjectProjectsSerializer()
        projects = serializer.get_projects(access_token)
        formatted_projects = []
        for p in projects['_embedded']['elements']:
            formatted_projects.append(f"Project ID: {p['id']}, Project Name: {p['name']}")
        
        return Response(formatted_projects)


class filter_tasks_by_project(APIView):
    def get(self, request, project_id):
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
                task = f"Task ID: {t['id']}, Subject: {t['subject']}, Project: {t['_links']['project']['title']}, Type: {t['_links']['type']['title']}, Status: {t['_links']['status']['title']}"
                formatted_tasks.append(task)
            
            return Response(formatted_tasks)
        
        except requests.exceptions.HTTPError as e:
            return Response({"detail": str(e)}, status=e.response.status_code)


class create_time_entry(APIView):
    def post(self, request):
        serializer = TimeEntrySerializer(data=request.data)
        if serializer.is_valid():
            try:
                access_token = request.session.get('access_token')
                if not access_token:
                    return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
                
                work_package_id = serializer.validated_data.get('workPackageId')
                data = {
                    "comment": {
                        "raw": serializer.validated_data["comment"]
                    },
                    "spentOn": serializer.validated_data["spentOn"].isoformat(),
                    "hours": "PT{}H".format(serializer.validated_data["hours"].total_seconds() // 3600),
                    "_links": {
                        "workPackage": {
                            "href": f"/api/v3/work_packages/{work_package_id}"
                        }
                    }
                }
                
                response = requests.post('https://bsts.openproject.com/api/v3/time_entries', json=data, headers={'Authorization': f'Bearer {access_token}'})
                
                if response.status_code == 201:
                    return Response(response.json(), status=status.HTTP_201_CREATED)
                else:
                    # Log detailed error response for debugging
                    print(f"Failed to create time entry: {response.status_code} - {response.text}")
                    return Response({"detail": "Failed to create time entry"}, status=status.HTTP_400_BAD_REQUEST)
            
            except requests.exceptions.RequestException as e:
                # Log detailed error for debugging
                print(f"RequestException: {str(e)}")
                return Response({"detail": "Failed to create time entry", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# this update task didn't worked
# @api_view(['PATCH'])
# def update_task(request, task_id):
#     access_token = request.session.get('access_token')
#     if not access_token:
#         return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
#     task_url = f"https://bsts.openproject.com/api/v3/work_packages/{task_id}"
    
#     try:
#         # Fetch current task data to get lock version
#         current_task_response = requests.get(task_url, headers={"Authorization": f"Bearer {access_token}"})
#         current_task_response.raise_for_status()
#         current_task = current_task_response.json()
        
#         # Include lock version in request data
#         request.data['lock_version'] = current_task.get('lockVersion')
        
#         serializer = OpenProjectUpdateTaskSerializer(instance=current_task, data=request.data)

#         # Print or log request data and validated data for debugging
#         print(f"Request Data: {request.data}")
#         if serializer.is_valid():
#             print(f"Validated Data: {serializer.validated_data}")
        
#         if serializer.is_valid():
#             # Perform the update using the serializer's update method
#             updated_task = serializer.update(instance=current_task, validated_data=serializer.validated_data, access_token=access_token)
#             return Response(updated_task, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     except requests.exceptions.HTTPError as e:
#         print(f"HTTPError: {str(e)}")
#         return Response({"detail": str(e)}, status=e.response.status_code)
#     except KeyError as e:
#         print(f"KeyError: {str(e)}")
#         return Response({"detail": f"KeyError: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    

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