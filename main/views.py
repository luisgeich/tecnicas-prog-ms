import json
from bson.objectid import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import APIView

from django.http import JsonResponse, Http404
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

from mongoengine.errors import ValidationError

from .pipelines.student import innferStates, innferBehaviors
from .models import Student, Feature, StudentFeature, State, Behavior
from .serializers import StudentSerializer, FeatureSerializer, StudentFeatureSerializer, StateSerializer, BehaviorSerializer, BehaviorStateSerializer

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})
class StudentViews(APIView):
    def get(self, request):
        students = Student.objects.all()

        skip = request.GET.get('skip', None)
        limit = request.GET.get('limit', None)

        print('Skip', skip)
        print('Limit', limit)

        if skip:
            students = students.skip(int(skip))

        if limit:
            students = students.limit(int(limit))

        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        valid = serializer.is_valid()
        if valid:
            student = serializer.save()
            serialized_student = serializer.to_representation(student)
            
            return Response(serialized_student, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentDetailView(APIView):

    def get_object(self, id):
        try:
            return Student.objects.get(id=id)
        except Student.DoesNotExist:
            raise Http404
        except ValidationError as e:
            raise Http404

    def get(self, request, id):
        student = self.get_object(id)
        serializer = StudentSerializer(student)
        return Response(serializer.data)
    
    def put(self, request, id):
        student = self.get_object(id)
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        student = self.get_object(id)
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  

class FeatureViews(APIView):
    def get(self, request):
        feature = Feature.objects.all()

        domain = request.GET.get('domain', None)
        if domain:
            feature = feature.filter(domain=domain) 

        serializer = FeatureSerializer(feature, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FeatureSerializer(data=request.data)
        valid = serializer.is_valid()
        if valid:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FeatureDetailView(APIView):
    def get_object(self, id):
        try:
            return Feature.objects.get(id=id)
        except Feature.DoesNotExist:
            raise Http404
        except ValidationError as e:
            raise Http404

    def get(self, request, id):
        feature = self.get_object(id)
        serializer = FeatureSerializer(feature)
        return Response(serializer.data)

    def put(self, request, id):
        feature = self.get_object(id)
        serializer = FeatureSerializer(feature, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        feature = self.get_object(id)
        feature.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class StudentFeatureView(APIView):
    def get_student(self, id) -> Student:
        try:
            return Student.objects.get(id=id)
        except Student.DoesNotExist:
            raise Http404
        except ValidationError as e:
            raise Http404
        
    def get(self, request, id):   
        pipeline = [
            {
                '$match': {
                    '_id': ObjectId(id)
                }
            }, 
            
            {
                '$unwind': '$features'
            }, 
            
            {
                '$lookup': {
                    'from': 'feature', 
                    'localField': 'features.feature', 
                    'foreignField': '_id', 
                    'as': 'feature_info'
                }
            }, 
            
            {
                '$unwind': '$feature_info'
            }, 
            
            {
                '$project': {
                    '_id': 0, 
                    'id': { '$toString' : '$features.feature' }, 
                    'name': '$feature_info.name', 
                    'domain': '$feature_info.domain', 
                    'value': '$features.value'
                }
            }
        ]
        
        features = list(Student.objects().aggregate(pipeline))
        
        return Response(features)
    
    def post(self, request, id):

        student = self.get_student(id)
        invalids = []
        features = []

        for feature in request.data:
            serializer = StudentFeatureSerializer(data=feature)
            if serializer.is_valid():
                features.append(StudentFeature(**feature))

            else:
                invalids.append(serializer.errors)

        if len(invalids) > 0:
            return Response(invalids, status=status.HTTP_400_BAD_REQUEST)

        student.features = features
        student.save()
        
        return Response(request.data)
    
class StudentStateInferatorView(APIView):
    
    def get(self, request, idStudent = None): 

        pipeline = innferStates(idStudent=idStudent)
        studentsStates = list(Student.objects().aggregate(pipeline))
        
        for student in studentsStates:
            _student = Student.objects.get(id=student['_id'])
            _student.states = [ state["_id"] for state in student['states'] ]
            _student.save()

        outputStates = [
            {
                "id" : str(student['_id']),
                "age" : student["age"],
                "alias" : student['alias'],
                "gender" : student["gender"],
                "states" : [
                    {
                        "id" : str(state["_id"]), 
                        "name" : state["name"], 
                        "domain" : state["domain"], 
                    } for state in student['states']
                ]
            } for student in studentsStates
        ]

        if idStudent:
            return Response(outputStates[0])

        return Response(outputStates)
    
class StudentBehaviorInferatorView(APIView):
    
    def get(self, request, idStudent = None): 

        pipeline = innferBehaviors(idStudent=idStudent)
        try:
            studentsBehaviors = list(Student.objects().aggregate(pipeline))
        except:
            return Response(pipeline, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        for student in studentsBehaviors:
            _student = Student.objects.get(id=student['_id'])
            _student.behaviors = [ behavior["_id"] for behavior in student['behaviors'] ]
            _student.save()

        outputBehaviors = [
            {
                "id" : str(student['_id']),
                "age" : student["age"],
                "alias" : student['alias'],
                "gender" : student["gender"],
                "behaviors" : [
                    {
                        "id" : str(behavior["_id"]), 
                        "name" : behavior["name"], 
                        "domain" : behavior["domain"], 
                    } for behavior in student['behaviors']
                ]
            } for student in studentsBehaviors
        ]

        if idStudent:
            return Response(outputBehaviors[0])

        return Response(outputBehaviors)
    

class StateViews(APIView):
    def get(self, request):
        states = State.objects.all()
        domain = request.GET.get('domain', None)
        if domain:
            states = states.filter(domain=domain)
            
        serializer = StateSerializer(states, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StateSerializer(data=request.data)
        valid = serializer.is_valid()
        if valid:
            state = serializer.save()
            serialized_state = serializer.to_representation(state)
            
            return Response(serialized_state, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class StateDetailView(APIView):

    def get_object(self, id) -> State:
        try:
            return State.objects.get(id=id)
        except State.DoesNotExist:
            raise Http404
        except ValidationError as e:
            raise Http404

    def get(self, request, id):
        state = self.get_object(id)
        serializer = StateSerializer(state)
        return Response(serializer.data)
    
    def put(self, request, id):
        state = self.get_object(id)
        serializer = StateSerializer(state, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        state = self.get_object(id)
        state.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  
    

class BehaviorViews(APIView):
    def get(self, request):
        behaviors = Behavior.objects.all()
        serializer = BehaviorSerializer(behaviors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BehaviorSerializer(data=request.data)
        valid = serializer.is_valid()
        if valid:
            behavior = serializer.save()
            serialized_behavior = serializer.to_representation(behavior)
            
            return Response(serialized_behavior, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class BehaviorDetailView(APIView):

    def get_object(self, id) -> Behavior:
        try:
            return Behavior.objects.get(id=id)
        except Behavior.DoesNotExist:
            raise Http404
        except ValidationError as e:
            raise Http404

    def get(self, request, id):
        behavior = self.get_object(id)
        serializer = BehaviorSerializer(behavior)
        return Response(serializer.data)
    
    def put(self, request, id):
        behavior = self.get_object(id)
        serializer = BehaviorSerializer(behavior, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        behavior = self.get_object(id)
        behavior.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  