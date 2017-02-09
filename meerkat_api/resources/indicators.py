from flask_restful import Resource

class Indicators(Resource):
    def get(self, variable, location):
        return {"Test":42}
