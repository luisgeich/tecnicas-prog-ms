from bson.objectid import ObjectId

def getUniqueFeatures() -> list:
    query = [
        {
            '$unwind': '$features'
        }, 

        {
            '$group': {
                '_id': '$_id', 
                'alias': {
                    '$first': '$alias'
                }, 
                'age': {
                    '$first': '$age'
                }, 
                'gender': {
                    '$first': '$gender'
                }, 
                'features': {
                    '$addToSet': {
                        'feature': '$features.feature', 
                        'value': '$features.value'
                    }
                }
            }
        }
    ]

    return query

def getUniqueStates() -> list:
    query = [
        {
            '$unwind': '$states'
        },
        {
            "$group" : {
                "_id": "$_id",
                "alias": {
                    "$first": "$alias",
                },
                "age": {
                    "$first": "$age",
                },
                "gender": {
                    "$first": "$gender",
                },
                "states": {
                    "$addToSet": "$states",
                }
            }
        }
    ]

    return query

def joinStates(_as = "states") -> list:
    query = [
        {
            '$unwind' : "$features"
        },
        {
            '$lookup': {
                'from': 'state', 
                'localField': 'features.feature', 
                'foreignField': 'features.feature', 
                'as': _as
            }
        }
    ]
    return query

def joinBehaviors(_as = "behavior") -> list:
    query = [
        {
            '$lookup': {
                'from': 'behavior', 
                'localField': 'states', 
                'foreignField': 'states.state', 
                'as': _as
            }
        }
    ]
    return query

def featuresConditions(operatorPath, basePath, valuePath) -> list:

    operators = ['gte', 'lte', 'lt', 'gt', 'eq']
    conditions = []

    for operator in operators:
        conditions.append(
            {
                '$cond': [
                    { '$eq': [  operatorPath, operator ] }, 
                    { f'${operator}' : [ valuePath, basePath ] }, 
                    False
                ]
            }
        )

    return conditions 

def innferStates(idStudent = None) -> list:
    query = []

    if idStudent:
        query += [
            {
                '$match' : {
                    "_id" : ObjectId(idStudent)
                }
            }
        ]

    query += getUniqueFeatures()
    query += joinStates('states')

    query += [
        {
            '$unwind' : '$states'
        },
        {
            '$unwind' : '$states.features'
        },
        {
            '$addFields': {
                'featuresMatched': {
                    '$or' : featuresConditions(
                        basePath="$states.features.base",
                        operatorPath="$states.features.operator",
                        valuePath="$features.value"
                    )
                }
            }
        },
        {
            '$group': {
                '_id': {
                    'student': '$_id', 
                    'state': '$states._id'
                }, 
                'alias': {
                    '$first': '$alias'
                }, 
                'age': {
                    '$first': '$age'
                }, 
                'gender': {
                    '$first': '$gender'
                }, 
                'state_name': {
                    '$first': '$states.name'
                }, 
                'state_domain': {
                    '$first': '$states.domain'
                }, 
                'features': {
                    '$push': '$featuresMatched'
                }
            }
        }, 
        
        {
            '$match': {
                '$expr': {
                    '$allElementsTrue': '$features'
                }
            }
        }, 
        
        {
            '$project': {
                '_id': '$_id.student', 
                'age': 1, 
                'alias': 1, 
                'gender': 1, 
                'state': {
                    '_id': '$_id.state', 
                    'name': '$state_name', 
                    'domain': '$state_domain'
                }
            }
        }, 
        
        {
            '$group': {
                '_id': '$_id', 
                'alias': {
                    '$first': '$alias'
                }, 
                'age': {
                    '$first': '$age'
                }, 
                'gender': {
                    '$first': '$gender'
                }, 
                'states': {
                    '$addToSet': '$state'
                }
            }
        }
    ]

    return query

def innferBehaviors(idStudent = None) -> list:

    query = []
    if idStudent:
        query += [
            {
                '$match' : {
                    "_id" : ObjectId(idStudent)
                }
            }
        ]

    query += getUniqueStates()
    query += joinBehaviors('behavior')

    query += [
        {
            '$unwind': '$behavior'
        }, 
        
        {
            '$match': {
                '$expr': {
                    '$eq': [
                        {
                            '$size': {
                                '$setIntersection': [
                                    '$behavior.states.state', '$states'
                                ]
                            }
                        }, {
                            '$size': '$behavior.states'
                        }
                    ]
                }
            }
        }, 
        
        {
            '$project': {
                'behavior.states': 0
            }
        }, 
        
        {
            '$group': {
                '_id': '$_id', 
                'alias': {
                    '$first': '$alias'
                }, 
                'age': {
                    '$first': '$age'
                }, 
                'gender': {
                    '$first': '$gender'
                }, 
                'behaviors': {
                    '$addToSet': '$behavior'
                }
            }
        }
    ]

    return query