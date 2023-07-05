from backend import settings
from mongoengine import Document, fields, connect, EmbeddedDocument

class Feature(Document):
    name = fields.StringField(max_length=150)
    domain = fields.StringField(max_length=150)
    unit = fields.StringField(max_length=150)

    class Meta:
        name = "feature"


class StudentFeature(EmbeddedDocument):
    feature = fields.ReferenceField(Feature)
    value = fields.DynamicField()

    class Meta:
        id_field = False

class Student(Document):
    
    alias = fields.StringField(max_length=10)
    age = fields.IntField()
    gender = fields.StringField(max_length=2)
    features = fields.ListField(fields.EmbeddedDocumentField(StudentFeature))
    states = fields.ListField(fields.ReferenceField("State"))
    behaviors = fields.ListField(fields.ReferenceField("Behavior"))

    def update_features(self, features):
        self.features = features
        self.save()

    class Meta:
        name =  "student"

class StateFeature(EmbeddedDocument):
    feature = fields.ReferenceField(Feature)
    base = fields.DynamicField()
    operator = fields.StringField()

    class Meta:
        id_field = False

class State(Document):
    name = fields.StringField(max_length=150)
    domain = fields.StringField(max_length=150)
    features = fields.ListField(fields.EmbeddedDocumentField(StateFeature))

    class Meta:

        name =  "state"

class BehaviorState(EmbeddedDocument):
    state = fields.ReferenceField(State)
    required = fields.BooleanField()

    class Meta:
        id_field = False
        
class Behavior(Document):
    name = fields.StringField(max_length=150)
    domain = fields.StringField(max_length=150)
    states = fields.ListField(fields.EmbeddedDocumentField(BehaviorState))


    class Meta:
        name =  "behavior"

try:
    connect(
        db=settings.DATABASES['default']['NAME'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        username=settings.DATABASES['default']['USERNAME'],
        password=settings.DATABASES['default']['PASSWORD']
    )
    
except Exception as e:
    print('UNABLE TO CONNECT TO DATABASE', e)