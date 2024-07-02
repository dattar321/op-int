import os 
import json
from rest_framework import serializers
import requests
from datetime import datetime
from isodate import duration_isoformat, parse_duration

class OpenProjectAuthorizeSerializer(serializers.Serializer):
    authorization_url = serializers.CharField()

class OpenProjectCallbackSerializer(serializers.Serializer):
    code = serializers.CharField()

    def create(self, validated_data):
        redirect_uri = os.getenv('redirect_uri') 
        # scope = os.getenv('scope') 
        token_url = "https://bsts.openproject.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "code": validated_data['code'],
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        response = requests.post(token_url, data=data)
        token_response = response.json()
        access_token = token_response.get("access_token")

        return {"access_token": access_token}

class OpenProjectProjectsSerializer(serializers.Serializer):

    def get_projects(self, access_token):
        projects_url = "https://bsts.openproject.com/api/v3/projects"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(projects_url, headers=headers)
        return response.json()

class OpenProjectTasksSerializer(serializers.Serializer):

    def get_tasks(self, access_token):
        tasks_url = "https://bsts.openproject.com/api/v3/work_packages"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(tasks_url, headers=headers)
        return response.json()
    


class TimeEntrySerializer(serializers.Serializer):
    comment = serializers.CharField()
    spentOn = serializers.DateField()
    hours = serializers.DurationField()
    workPackageId = serializers.IntegerField(write_only=True)

    def create(self, validated_data):
        work_package_id = validated_data.pop('workPackageId')
        data = {
            "comment": {
                "raw": validated_data["comment"]
            },
            "spentOn": validated_data["spentOn"].isoformat(),
            "hours": "PT{}H".format(validated_data["hours"].total_seconds() // 3600),
            "_links": {
                "workPackage": {
                    "href": f"/api/v3/work_packages/{work_package_id}"
                }
            }
        }
        
        response = requests.post('https://bsts.openproject.com/api/v3/time_entries', json=data, headers={'Authorization': 'Bearer YOUR_ACCESS_TOKEN'})

        if response.status_code != 201:
            # Log detailed error response for debugging
            print(f"Failed to update task: {response.status_code} - {response.text}")
            response.raise_for_status()  # Raise an error for bad responses
        if response.status_code == 201:
            return response.json()
        else:
            raise serializers.ValidationError('Failed to create time entry')

# this OpenProjectUpdateTaskSerializer doesn't work 

# class OpenProjectUpdateTaskSerializer(serializers.Serializer):
#     subject = serializers.CharField(required=False)
#     description = serializers.CharField(required=False)
#     type_id = serializers.IntegerField(required=False)
#     status_id = serializers.IntegerField(required=False)
#     lock_version = serializers.IntegerField(required=False)

#     def update(self, instance, validated_data, access_token):
#         task_id = instance['id']
#         tasks_url = f"https://bsts.openproject.com/api/v3/work_packages/{task_id}"
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#         data = {
#             "subject": validated_data.get('subject', instance['subject']),
#             "description": {
#                 "raw": validated_data.get('description', instance['description']['raw'])
#             },
#             "_links": {
#                 "type": {
#                     "href": f"/api/v3/types/{validated_data.get('type_id', instance['_links']['type']['href'].split('/')[-1])}"
#                 },
#                 "status": {
#                     "href": f"/api/v3/statuses/{validated_data.get('status_id', instance['_links']['status']['href'].split('/')[-1])}"
#                 }
#             },
#             "lockVersion": validated_data['lock_version']
#         }

#         response = requests.patch(tasks_url, json=data, headers=headers)
#         response.raise_for_status()  # Raise an error for bad responses
#         if response.status_code != 200:
#             # Log detailed error response for debugging
#             print(f"Failed to update task: {response.status_code} - {response.text}")
#             response.raise_for_status()  # Raise an error for bad responses
        
#         return response.json()



# class OpenProjectCreateProjectSerializer(serializers.Serializer):
#     name = serializers.CharField()
#     identifier = serializers.CharField()
#     description = serializers.CharField()

#     def create(self, validated_data, access_token):
#         projects_url = "https://bsts.openproject.com/api/v3/projects"
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#         data = {
#             "name": validated_data['name'],
#             "identifier": validated_data['identifier'],
#             "description": {
#                 "raw": validated_data['description']
#             }
#         }
        
#         response = requests.post(projects_url, json=data, headers=headers)
#         response.raise_for_status()  # Raises an error for bad responses
#         return response.json()



# class OpenProjectCreateTaskSerializer(serializers.Serializer):
#     subject = serializers.CharField()
#     description = serializers.CharField()
#     project_id = serializers.IntegerField()
#     type_id = serializers.IntegerField()
#     status_id = serializers.IntegerField()

#     def create(self, validated_data, access_token):
#         tasks_url = "https://bsts.openproject.com/api/v3/work_packages"
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#         data = {
#             "subject": validated_data['subject'],
#             "description": {
#                 "raw": validated_data['description']
#             },
#             "_links": {
#                 "project": {
#                     "href": f"/api/v3/projects/{validated_data['project_id']}"
#                 },
#                 "type": {
#                     "href": f"/api/v3/types/{validated_data['type_id']}"
#                 },
#                 "status": {
#                     "href": f"/api/v3/statuses/{validated_data['status_id']}"
#                 }
#             }
#         }
        
#         response = requests.post(tasks_url, json=data, headers=headers)
#         response.raise_for_status()  # Raises an error for bad responses
#         return response.json()

# class OpenProjectUpdateProjectSerializer(serializers.Serializer):
#     name = serializers.CharField(required=False)
#     description = serializers.CharField(required=False)

#     def update(self, instance, validated_data, access_token):
#         project_url = f"https://bsts.openproject.com/api/v3/projects/{instance['id']}"
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#         data = {
#             "name": validated_data.get('name', instance['name']),
#             "description": validated_data.get('description', instance['description']),
#         }
        
#         response = requests.patch(project_url, json=data, headers=headers)
#         response.raise_for_status()
#         return response.json()
    

# class OpenProjectUpdateTaskSerializer(serializers.Serializer):
#     subject = serializers.CharField(required=False)
#     description = serializers.CharField(required=False)
#     type_id = serializers.IntegerField(required=False)
#     status_id = serializers.IntegerField(required=False)
#     lock_version = serializers.IntegerField(required=False)
#     estimatedTime = serializers.CharField(required=False)
#     # derivedEstimatedTime = serializers.DurationField(required=False)
#     # derivedRemainingTime = serializers.DurationField(required=False)

#     def update(self, instance, validated_data, access_token):
#         instance['subject'] = validated_data.get('subject', instance.get('subject'))
#         instance['description']['raw'] = validated_data.get('description', instance['description']['raw'])
#         instance['_links']['type']['href'] = f"/api/v3/types/{validated_data.get('type_id', instance['_links']['type']['href'].split('/')[-1])}"
#         instance['_links']['status']['href'] = f"/api/v3/statuses/{validated_data.get('status_id', instance['_links']['status']['href'].split('/')[-1])}"
#         instance['lockVersion'] = validated_data.get('lock_version', instance['lockVersion'])
        
#         # Handle estimatedTime if needed
#         instance['estimatedTime'] = validated_data.get('estimatedTime', instance.get('estimatedTime'))
        
#         # # Handle derivedEstimatedTime
#         # derived_estimated_time = validated_data.get('derivedEstimatedTime')
#         # if derived_estimated_time:
#         #     instance['derivedEstimatedTime'] = duration_isoformat(derived_estimated_time)
        
#         # # Handle derivedRemainingTime
#         # derived_remaining_time = validated_data.get('derivedRemainingTime')
#         # if derived_remaining_time:
#         #     instance['derivedRemainingTime'] = duration_isoformat(derived_remaining_time)



#         # Perform API call to update the task
#         task_id = instance['id']
#         tasks_url = f"https://bsts.openproject.com/api/v3/work_packages/{task_id}"
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#         response = requests.patch(tasks_url, data=json.dumps(instance), headers=headers)
        
#         if response.status_code != 200:
#             # Log detailed error response for debugging
#             print(f"Failed to update task: {response.status_code} - {response.text}")
#             response.raise_for_status()  # Raise an error for bad responses
        
#         return response.json()

