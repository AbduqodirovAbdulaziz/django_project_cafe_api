from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CafeTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Login javobida frontend uchun kerakli user metadata ni ham qaytaradi.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.id
        token["username"] = user.username
        token["role"] = getattr(user, "role", "")
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": getattr(user, "role", ""),
            "is_staff": user.is_staff,
            "is_active": user.is_active,
        }
        return data
