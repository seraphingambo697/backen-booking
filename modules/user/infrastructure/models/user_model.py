import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserModelManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **kw):
        user = self.model(email=self.normalize_email(email),
                          first_name=first_name, last_name=last_name, **kw)
        if password: user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, first_name, last_name, password, **kw):
        kw.update({"is_admin": True, "is_staff": True, "is_superuser": True})
        return self.create_user(email, first_name, last_name, password, **kw)

class UserModel(AbstractBaseUser):
    class Meta:
        app_label = "user_infrastructure"
        db_table  = "users"
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email      = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    phone      = models.CharField(max_length=20, blank=True, default="")
    password   = models.CharField(max_length=255)
    is_active  = models.BooleanField(default=True)
    is_admin   = models.BooleanField(default=False)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects    = UserModelManager()
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    def __str__(self): return f"{self.first_name} {self.last_name} <{self.email}>"
    def has_perm(self, p, obj=None): return self.is_admin
    def has_module_perms(self, l): return self.is_admin