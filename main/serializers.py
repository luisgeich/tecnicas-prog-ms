from rest_framework import serializers
from .models import Student, Feature, StudentFeature, State, StateFeature, Behavior, BehaviorState

class StudentFeatureSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    feature = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.all())

    def get_value(self, obj):
        return obj.value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        value = self.get_value(instance)
        representation['value'] = value
        return representation

    def to_internal_value(self, data):
        value = data.get('value')
        # Convert the value to the appropriate type based on your logic
        return {'value': value, 'feature': data.get('feature')}


    class Meta:
        model = StudentFeature
        fields = "__all__"

class StudentSerializer(serializers.Serializer):

    id = serializers.CharField(read_only=True)  # Include the ID field

    alias = serializers.CharField(max_length=10)
    age = serializers.IntegerField(min_value=0)
    gender = serializers.CharField(max_length=2)
    features = StudentFeatureSerializer(many=True, required=False)

    states = serializers.SerializerMethodField()
    behaviors = serializers.SerializerMethodField()

    def get_states(self, obj):
        my_objects = obj.states
        serialized_objects = StateSerializer(my_objects, many=True).data
        return serialized_objects

    def get_behaviors(self, obj):
        my_objects = obj.behaviors
        serialized_objects = BehaviorSerializer(my_objects, many=True).data
        return serialized_objects


    def create(self, validated_data):
        return Student.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        
        validated_data.pop('alias', None)
        validated_data.pop('features', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['features'] = [
            {
                'feature': str(feature['feature']), 
                'value': feature['value']
            } for feature in data['features']
        ]

        data['states'] = [
            {
                'id': str(state['id']), 
                'name': state['name']
            } for state in data['states']
        ]

        data['behaviors'] = [
            {
                'id': str(behavior['id']), 
                'name': behavior['name'],
                'domain': behavior['domain']
            } for behavior in data['behaviors']
        ]
        
        return data

    class Meta:
        model = Student
        fields = "__all__"
        
        
class StateFeatureSerializer(serializers.Serializer):
    base = serializers.CharField()
    operator = serializers.CharField()
    feature = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.all())

    def get_base(self, obj):
        # Define your custom logic here to return the appropriate base value
        # based on the type of 'obj'
        return obj.base

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        base = self.get_base(instance)
        representation['base'] = base
        return representation

    def to_internal_value(self, data):
        base = data.get('base')
        # Convert the base value to the appropriate type based on your logic
        return {'base': base, 'operator': data.get('operator'), 'feature': data.get('feature')}



    class Meta:
        model = StudentFeature
        fields = "__all__"

class StateSerializer(serializers.Serializer):

    id = serializers.CharField(read_only=True)  # Include the ID field
    name = serializers.CharField(max_length=150)
    domain = serializers.CharField(max_length=150)
    features = StateFeatureSerializer(many=True, required=True)

    def create(self, validated_data):
        return State.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        features = validated_data.pop('features', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.features = []
        for feature in features:
            instance.features.append(StateFeature(**feature))

        instance.save()
        return instance
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['features'] = [
            {
                'feature': str(feature['feature']), 
                'base': feature['base'],
                'operator' : feature['operator']
            } for feature in data['features']
        ]
        
        return data

    class Meta:
        model = State
        fields = "__all__"

class BehaviorStateSerializer(serializers.Serializer):
    required = serializers.BooleanField(required=False, default=True)
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())

    class Meta:
        model = BehaviorState
        fields = "__all__"

class BehaviorSerializer(serializers.Serializer):

    id = serializers.CharField(read_only=True)  # Include the ID field
    name = serializers.CharField(max_length=150)
    domain = serializers.CharField(max_length=150)
    states = BehaviorStateSerializer(many=True, required=True)

    def create(self, validated_data):
        return Behavior.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        states = validated_data.pop('states', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.states = []
        for feature in states:
            instance.states.append(BehaviorState(**feature))

        instance.save()
        return instance
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['states'] = [
            {
                'state': str(state['state']), 
                'required': state['required'],
            } for state in data['states']
        ]
        
        return data

    class Meta:
        model = State
        fields = "__all__"


class FeatureSerializer(serializers.Serializer):

    id = serializers.CharField(read_only=True)  # Include the ID field
    name = serializers.CharField()
    domain = serializers.CharField()  
    unit = serializers.CharField(required=False)  
    
    class Meta:
        model = Feature
        fields = "__all__"

    def create(self, validated_data):
        return Feature.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

