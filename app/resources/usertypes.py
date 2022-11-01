from typing import List
from flask import jsonify, request
from flask.views import MethodView
from webargs import fields, validate
from webargs.flaskparser import parser, use_args, use_kwargs

from app.models import UserType
from app.schemas import UserRoleSchema
from app.wrappers import admin_only


class UserTypesAPI(MethodView):
    @admin_only
    def get(self: None) -> List[UserType]:
        """Get user types available

        Returns:
            List[UserType]: List of <UserType> as JSON
        """
        uts = UserType.query.all()
        return jsonify(UserRoleSchema(many=True).dump(uts))

    @admin_only
    def post(self: None) -> UserType:
        """Create a new user UserType.

        Returns:
            UserType: <UserType> as JSON.
        """
        args = parser.parse(UserRoleSchema(), location="json")
        try:
            user_type = UserType().create(UserType, args)
            result = UserType.query.get(user_type.id)
            return jsonify(UserRoleSchema().dump(result))
        except Exception as e:
            return jsonify(e)
