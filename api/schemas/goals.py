from marshmallow import Schema, fields
class GoalSchema(Schema):
        name = fields.String(required=True)
        amount = fields.Float(required=True)
        deadline = fields.Date(required=False)